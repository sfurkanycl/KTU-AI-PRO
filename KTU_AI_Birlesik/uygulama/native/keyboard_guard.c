/*
 * keyboard_guard.c
 * Ogrenme molasi sirasinda belirli Windows cikis kisayollarini engeller.
 * Kullanici modu WH_KEYBOARD_LL kancasi; Ctrl+Alt+Del ENGELLENEMEZ.
 *
 * Derleme (MinGW-w64):  gcc -shared -O2 -o keyboard_guard.dll keyboard_guard.c -luser32
 * Derleme (MSVC):       cl /LD /O2 keyboard_guard.c user32.lib
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#ifdef _MSC_VER
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __declspec(dllexport)
#endif

static HINSTANCE        g_module    = NULL;
static HHOOK            g_hook      = NULL;
static HANDLE           g_thread    = NULL;
static HANDLE           g_ready     = NULL;
static DWORD            g_thread_id = 0;
static volatile LONG    g_blocked   = 0;      /* engellenen deneme sayisi */
static volatile LONG    g_active    = 0;
static ULONGLONG        g_deadline  = 0;      /* 0 = sinirsiz; doluysa sure dolunca kanca kendini pasifler */

BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID reserved) {
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        g_module = h;
        DisableThreadLibraryCalls(h);
    }
    return TRUE;
}

static int should_block(const KBDLLHOOKSTRUCT *k) {
    DWORD vk   = k->vkCode;
    int   alt  = (k->flags & LLKHF_ALTDOWN) != 0;
    int   ctrl = (GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0;
    int   shift= (GetAsyncKeyState(VK_SHIFT)   & 0x8000) != 0;

    if (vk == VK_LWIN || vk == VK_RWIN || vk == VK_APPS) return 1;   /* Win tusu, menu tusu */
    if (alt && vk == VK_TAB)    return 1;                            /* Alt+Tab   */
    if (alt && vk == VK_ESCAPE) return 1;                            /* Alt+Esc   */
    if (alt && vk == VK_F4)     return 1;                            /* Alt+F4    */
    if (ctrl && vk == VK_ESCAPE) return 1;                           /* Ctrl+Esc (Baslat) */
    if (ctrl && shift && vk == VK_ESCAPE) return 1;                  /* Gorev Yoneticisi */
    return 0;
}

static LRESULT CALLBACK hook_proc(int code, WPARAM wp, LPARAM lp) {
    if (code == HC_ACTION) {
        /* Guvenlik agi: sure dolduysa hicbir sey engelleme */
        if (g_deadline != 0 && GetTickCount64() > g_deadline)
            return CallNextHookEx(g_hook, code, wp, lp);

        const KBDLLHOOKSTRUCT *k = (const KBDLLHOOKSTRUCT *)lp;
        if (should_block(k)) {
            if (wp == WM_KEYDOWN || wp == WM_SYSKEYDOWN)
                InterlockedIncrement(&g_blocked);
            return 1;   /* tusu yut */
        }
    }
    return CallNextHookEx(g_hook, code, wp, lp);
}

static DWORD WINAPI hook_thread(LPVOID unused) {
    (void)unused;
    MSG msg;
    /* Mesaj kuyrugunu SetEvent'ten once olustur. Boylece guard_stop hemen
       cagrilsa bile PostThreadMessage(WM_QUIT) yarista kaybolmaz. */
    PeekMessageW(&msg, NULL, WM_USER, WM_USER, PM_NOREMOVE);
    g_hook = SetWindowsHookExW(WH_KEYBOARD_LL, hook_proc, g_module, 0);
    SetEvent(g_ready);
    if (!g_hook) return 1;

    /* Sure dolunca yalnizca tuslari serbest birakmak yerine kancayi ve
       mesaj dongusunu da gercekten kapat. */
    UINT_PTR timer_id = 0;
    if (g_deadline != 0) {
        ULONGLONG now = GetTickCount64();
        ULONGLONG remaining = g_deadline > now ? g_deadline - now : 1;
        UINT delay = remaining > USER_TIMER_MAXIMUM ? USER_TIMER_MAXIMUM : (UINT)remaining;
        timer_id = SetTimer(NULL, 1, delay, NULL);
    }

    while (GetMessageW(&msg, NULL, 0, 0) > 0) {
        if (msg.message == WM_TIMER && timer_id != 0 && msg.wParam == timer_id) {
            InterlockedExchange(&g_active, 0);
            break;
        }
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    if (timer_id != 0) KillTimer(NULL, timer_id);
    UnhookWindowsHookEx(g_hook);
    g_hook = NULL;
    g_thread_id = 0;
    return 0;
}

/* max_seconds: 0 = sinirsiz, >0 = bu sure sonunda kanca kendiliginden etkisiz kalir.
 * Donus: 1 basarili, 0 basarisiz */
EXPORT int guard_start(unsigned int max_seconds) {
    /* Zaman asimiyla bitmis onceki is parcaciginin handle'ini temizle. */
    if (g_thread && WaitForSingleObject(g_thread, 0) == WAIT_OBJECT_0) {
        CloseHandle(g_thread);
        g_thread = NULL;
    }
    if (InterlockedCompareExchange(&g_active, 1, 0) != 0) return 1;   /* zaten acik */

    g_blocked  = 0;
    g_deadline = max_seconds ? GetTickCount64() + (ULONGLONG)max_seconds * 1000ULL : 0;
    g_ready    = CreateEventW(NULL, TRUE, FALSE, NULL);
    if (!g_ready) {
        InterlockedExchange(&g_active, 0);
        return 0;
    }
    g_thread   = CreateThread(NULL, 0, hook_thread, NULL, 0, &g_thread_id);
    if (!g_thread) {
        CloseHandle(g_ready);
        g_ready = NULL;
        InterlockedExchange(&g_active, 0);
        return 0;
    }

    DWORD ready_result = WaitForSingleObject(g_ready, 2000);
    CloseHandle(g_ready); g_ready = NULL;

    if (ready_result != WAIT_OBJECT_0 || !g_hook) {
        PostThreadMessageW(g_thread_id, WM_QUIT, 0, 0);
        WaitForSingleObject(g_thread, 1000);
        CloseHandle(g_thread); g_thread = NULL;
        g_thread_id = 0;
        InterlockedExchange(&g_active, 0);
        return 0;
    }
    return 1;
}

EXPORT void guard_stop(void) {
    InterlockedExchange(&g_active, 0);
    if (!g_thread) return;
    if (g_thread_id != 0) PostThreadMessageW(g_thread_id, WM_QUIT, 0, 0);
    if (WaitForSingleObject(g_thread, 2000) == WAIT_OBJECT_0) {
        CloseHandle(g_thread);
        g_thread = NULL;
        g_thread_id = 0;
    }
}

EXPORT int guard_is_active(void)     { return (int)g_active; }
EXPORT int guard_blocked_count(void) { return (int)g_blocked; }
