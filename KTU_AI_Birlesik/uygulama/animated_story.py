"""Resizable illustrated story scenes; animation follows the spoken lesson stage."""
import math
from PyQt6.QtCore import Qt,QTimer,QRectF,QPointF
from PyQt6.QtGui import QPainter,QColor,QPen,QFont,QFontMetricsF,QPainterPath
from PyQt6.QtWidgets import QWidget

class StoryScene(QWidget):
    def __init__(self,question,parent=None):
        super().__init__(parent);self.question=question;self.step=0;self.frame=0
        self.setMinimumHeight(330)
        self.timer=QTimer(self);self.timer.setInterval(40);self.timer.timeout.connect(self.advance)
        self.answer=str(question['choices'][question['answer']])
        self.helping=any(word in (question['text']+' '+self.answer).casefold() for word in ('yardım','paylaş','kalem verdi','paylas'))
    @property
    def phase(self):return self.step
    def _advance(self):self.advance()
    def advance(self):self.frame=(self.frame+1)%160;self.update()
    def set_step(self,step):self.step=step;self.frame=0;self.update()
    def showEvent(self,event):self.timer.start();super().showEvent(event)
    def hideEvent(self,event):self.timer.stop();super().hideEvent(event)
    def text_box(self,p,rect,text,size=18,color='#243653'):
        p.setPen(QColor(color))
        flags=int(Qt.AlignmentFlag.AlignCenter)|int(Qt.TextFlag.TextWordWrap)
        while size>10:
            font=QFont('Segoe UI',size);metrics=QFontMetricsF(font)
            if metrics.boundingRect(rect,flags,text).height()<=rect.height()-8:break
            size-=1
        p.setFont(QFont('Segoe UI',size));p.drawText(rect,flags,text)
    def child(self,p,x,y,shirt,arm=0):
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(shirt));p.drawRoundedRect(QRectF(x-30,y+35,60,72),18,18)
        p.setBrush(QColor('#f5c89d'));p.drawEllipse(QRectF(x-29,y-25,58,62))
        p.setBrush(QColor('#583e34'));p.drawChord(QRectF(x-31,y-30,62,48),0,180*16)
        p.setPen(QPen(QColor('#243653'),3));p.drawPoint(QPointF(x-10,y+2));p.drawPoint(QPointF(x+10,y+2));p.drawArc(QRectF(x-11,y+5,22,15),180*16,180*16)
        p.setPen(QPen(QColor(shirt),12,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(x-24,y+53),QPointF(x-45,y+80-arm));p.drawLine(QPointF(x+24,y+53),QPointF(x+48,y+70-arm))
        p.setPen(QPen(QColor('#344b6d'),13,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap));p.drawLine(QPointF(x-15,y+102),QPointF(x-20,y+137));p.drawLine(QPointF(x+15,y+102),QPointF(x+20,y+137))
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=self.width(),self.height();p.fillRect(self.rect(),QColor('#f2f7ff'))
        header=QRectF(14,12,w-28,76);p.setBrush(QColor('#ffffff'));p.setPen(QPen(QColor('#d4c7fa'),2));p.drawRoundedRect(header,16,16)
        self.text_box(p,header.adjusted(14,5,-14,-5),self.question['text'],18)
        floor=h-112;top=105;available=max(150,floor-top)
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#deede5'));p.drawRoundedRect(QRectF(14,top,w-28,available),18,18)
        # Decorative classroom board and floor keep the story legible on every window size.
        p.setBrush(QColor('#9bcab6'));p.drawRoundedRect(QRectF(w*.33,top+12,w*.34,available*.40),12,12)
        p.setPen(QPen(QColor('#fff7e3'),4));p.drawLine(QPointF(w*.38,top+35),QPointF(w*.62,top+35))
        p.drawLine(QPointF(w*.38,top+53),QPointF(w*.55,top+53))
        scale=min(1.1,(available-22)/180);base=top+available-30-137*scale
        p.save();p.translate(w*.27,base);p.scale(scale,scale);self.child(p,0,0,'#8061d8',10 if self.step else 0);p.restore()
        p.save();p.translate(w*.73,base);p.scale(scale,scale);self.child(p,0,0,'#36a89a',10 if self.step else 0);p.restore()
        t=min(1,(self.frame%80)/60) if self.step==1 else 1 if self.step>=2 else 0
        if self.helping:
            x=w*.32+(w*.36)*t;y=base+65*scale-18*math.sin(t*math.pi)
            p.setPen(QPen(QColor('#ffb43b'),9,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap));p.drawLine(QPointF(x-22,y),QPointF(x+22,y-8))
            p.setPen(QPen(QColor('#44506b'),4));p.drawLine(QPointF(x+22,y-8),QPointF(x+29,y-10))
        else:
            # A shared book opens as the children examine the information together.
            x=w*.5;y=top+available*.64+5*math.sin(self.frame*.08)
            p.setBrush(QColor('#fff8de'));p.setPen(QPen(QColor('#cf9f53'),3));p.drawRoundedRect(QRectF(x-58,y-32,116,64),7,7);p.drawLine(QPointF(x,y-30),QPointF(x,y+30))
            for offset in (-40,12):
                for row in range(3):p.drawLine(QPointF(x+offset,y-14+row*12),QPointF(x+offset+27,y-14+row*12))
        if self.step>=2:
            p.setPen(QColor('#e6a700'));p.setFont(QFont('Segoe UI',24,QFont.Weight.Bold));p.drawText(QRectF(w*.43,top+65,w*.14,44),int(Qt.AlignmentFlag.AlignCenter),'✓')
        footer=QRectF(14,h-99,w-28,86);p.setPen(QPen(QColor('#b7ded1'),2));p.setBrush(QColor('#ffffff'));p.drawRoundedRect(footer,16,16)
        caption=('Olayı gözlemleyelim. Sorudaki bilgileri birlikte düşünelim.' if self.step==0 else self.question.get('hint') or 'Hangi davranış veya bilgi soruya cevap oluyor?') if self.step<2 else self.question.get('explanation') or 'Doğru cevap: '+self.answer
        self.text_box(p,footer.adjusted(15,5,-15,-5),caption,18)
        p.end()
