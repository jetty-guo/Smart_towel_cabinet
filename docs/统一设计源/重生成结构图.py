from pathlib import Path
from html import escape as esc
import json,re,hashlib
R=Path(__file__).resolve().parent.parent; P=R/'图片'; E=R/'统一设计源';E.mkdir(exist_ok=True)
from pathlib import Path
from html import escape as e
import json
R=Path(__file__).resolve().parent.parent;P=R/'图片'
INK='#18364d';T='#087f86';A='#ad671c';BLUE='#426bc2';M='#587080';LINE='#d8e4ec';BG='#f4f8fb'
CAT=[]
class Fig:
 def __init__(self,n,title,sub,h=1080):
  self.n=n;self.title=title;self.h=h;self.s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="{h}" viewBox="0 0 1800 {h}" role="img"><title>{e(title)}</title><defs><marker id="a" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto-start-reverse"><path d="M0 0L9 4.5L0 9z" fill="{T}"/></marker><pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="10" stroke="#abc2cf" stroke-width="3"/></pattern></defs><rect width="1800" height="{h}" fill="{BG}"/>']
  self.text(65,74,f'{n:02d}  {title}',43,INK,True);self.text(65,120,sub,25,M)
 def text(self,x,y,text,size=27,color=INK,bold=False):
  self.s.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="PingFang SC,Heiti SC,Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}">{e(str(text))}</text>')
 def rect(self,x,y,w,h,fill='white',stroke=LINE,rx=12):self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>')
 def line(self,x1,y1,x2,y2,col=T,dash=False,arrow=False):self.s.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{col}" stroke-width="3"'+(' stroke-dasharray="10 8"' if dash else '')+(' marker-end="url(#a)"' if arrow else '')+'/>')
 def path(self,p,col=T,arrow=False,dash=False):self.s.append(f'<path d="{p}" fill="none" stroke="{col}" stroke-width="3"'+(' marker-end="url(#a)"' if arrow else '')+(' stroke-dasharray="9 7"' if dash else '')+'/>')
 def circle(self,x,y,r,fill='white',stroke=T):self.s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>')
 def box(self,x,y,w,h,title,lines=(),col=T):
  self.rect(x,y,w,h);self.rect(x,y,w,7,col,col,3)
  units=sum(1 if ord(c)>127 else .57 for c in title);sz=min(30,(w-44)/max(1,units));self.text(x+22,y+49,title,sz,col,True)
  for i,l in enumerate(lines):self.text(x+22,y+94+i*36,l,25)
 def dim(self,x1,y1,x2,y2,label):
  self.s.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{T}" stroke-width="2.5" marker-start="url(#a)" marker-end="url(#a)"/>')
  if y1==y2:
   self.line(x1,y1-12,x1,y1+12,M);self.line(x2,y2-12,x2,y2+12,M);self.text((x1+x2)/2-70,y1-18,label,26,T)
  else:
   self.line(x1-12,y1,x1+12,y1,M);self.line(x2-12,y2,x2+12,y2,M);self.s.append(f'<text transform="translate({x1-18} {(y1+y2)/2}) rotate(-90)" text-anchor="middle" fill="{T}" font-family="PingFang SC,Arial,sans-serif" font-size="26">{e(label)}</text>')
 def footer(self,t='功能与空间示意，非加工图；参数、比例和安全边界须由工程图与样机验证。'):
  self.line(65,self.h-72,1735,self.h-72,LINE);self.text(65,self.h-30,t,22,M)
 def save(self,stem,chapter,caption):
  self.footer();self.s.append('</svg>');name=f'{self.n:02d}_{stem}.svg';(P/name).write_text(''.join(self.s));CAT.append(dict(number=self.n,file=name,title=self.title,chapter=chapter,caption=caption))
def flow(n,title,sub,items,chapter,stem,caption):
 f=Fig(n,title,sub)
 for i,(t,ls) in enumerate(items):
  row=i//3;col=i%3 if row==0 else 2-i%3;x=65+col*570;y=205+row*335
  f.box(x,y,525,215,t,ls)
  if i in [0,1]:f.line(x+525,y+107,x+560,y+107,arrow=True)
  if i==2:f.line(x+263,y+215,x+263,y+325,arrow=True)
  if i in [3,4]:f.line(x,y+107,x-35,y+107,arrow=True)
 f.save(stem,chapter,caption)

# One shared normalized 3D layout: x left->right, y front->rear, z floor->top.
MODEL=json.loads((E/'单一产品布局.json').read_text())
REG=[]
def finish(f,name,chapter,caption):
 f.footer('LVT-ONE / V1.6 · 同一柜体与模块坐标；布局示意，毫米尺寸、公差、容量和安全距离待工程验证。')
 f.s.append('</svg>');(P/name).write_text(''.join(f.s));REG.append({'number':f.n,'file':name,'title':f.title,'chapter':chapter,'caption':caption})
def front(f,ox,oy,s=0.4,inside=False,focus=None):
 def rect(box,c,stroke=INK):
  x,y,z,w,d,h=box;f.rect(ox+x*s,oy+(1500-z-h)*s,w*s,h*s,c,stroke,4)
 f.rect(ox,oy,1000*s,1500*s,'#eef1f2',INK,15*s)
 f.rect(ox,oy+1440*s,1000*s,60*s,'#35444e',INK,0)
 if not inside:
  f.rect(ox+85*s,oy+20*s,840*s,1145*s,'#e1e7e9','#9eadb7',8*s)
  rect(MODEL['front']['pickup'],'#344955');rect(MODEL['front']['return'],'#344955')
  f.rect(ox+195*s,oy+452*s,318*s,45*s,'#fffdf5','#b8c5c7',5*s)
  f.path(f'M{ox+620*s} {oy+790*s}h{240*s}v{140*s}h{-240*s}Z','#7a919e')
  rect(MODEL['front']['lower_door'],'#e3e9eb');rect(MODEL['front']['qr'],'white')
  f.text(ox+120*s,oy+165*s,'Liveo',76*s,INK,True)
  f.text(ox+220*s,oy+560*s,'CLEAN TOWEL',28*s)
  f.text(ox+660*s,oy+1010*s,'RETURN',28*s)
  f.text(ox+815*s,oy+239*s,'QR',30*s);f.circle(ox+840*s,oy+310*s,14*s,'#8cd39d','#277e48')
  for x,z in [(950,930),(500,270)]:f.circle(ox+x*s,oy+(1500-z)*s,11*s,'#bec8cc',INK)
 else:
  for k,v in MODEL['modules'].items():
   # M1 and M2 share front projection: render M2 in front, show depths in side view.
   if k=='H03':continue
   rect(v['box'],v['color'] if not focus or k==focus else '#edf0f2')
   x,y,z,w,d,h=v['box'];f.text(ox+(x+14)*s,oy+(1500-z-h/2)*s,k,34*s,INK,True)
  # Sealed return chutes, not open paths across the clean zone.
  f.path(f'M{ox+750*s} {oy+990*s}V{oy+1200*s}',A,True)
  f.path(f'M{ox+630*s} {oy+1060*s}L{ox+280*s} {oy+1170*s}V{oy+1200*s}',A,True)
  f.line(ox+100*s,oy+1190*s,ox+900*s,oy+1190*s,INK,True)
  f.text(ox+135*s,oy+800*s,'独立封闭污巾通道',30*s,A)
  f.text(ox+135*s,oy+855*s,'不得穿过净巾接触面',28*s,A)
 return (ox,oy,s)
def side(f,ox,oy,s=.46):
 # rear left, public front right; one continuous side section of clean lane.
 def r(y,z,d,h,c):f.rect(ox+(700-y-d)*s,oy+(1500-z-h)*s,d*s,h*s,c,INK,3)
 f.rect(ox,oy,700*s,1500*s,'#f3f6f7',INK,5)
 for key in ['H01','H03','H06','H08']:
  x,y,z,w,d,h=MODEL['modules'][key]['box'];r(y,z,d,h,MODEL['modules'][key]['color'])
 # H02 bottom support; H04 at mouth; H05 bridge; H07 actuator and release gate.
 r(380,1150,25,80,'#e5ba7e');r(370,1135,20,8,'#8cafb9');r(100,1095,10,125,'#2c8186')
 f.path(f'M{ox+80*s} {oy+430*s}H{ox+555*s}V{oy+450*s}H{ox+640*s}V{oy+505*s}',T,True)
 for i in range(4):r(435,1170+i*45,200,30,'#fff7e7')
 f.text(ox+10,oy-18,'后方 ← 沿柜深送料 → 前方',23,T,True)
 f.text(ox+18,oy+570*s,'H01 / H02 / H03',21)
 f.text(ox+18,oy+645*s,'H04分离 → H05过渡',21)
 f.text(ox+18,oy+720*s,'H06保持 → H07释放',21)
 f.text(ox+18,oy+795*s,'H08接正面领巾口',21)
 f.text(ox+18,oy+1090*s,'下部为隔离的回收舱',21,A)
 f.text(ox+18,oy+1180*s,'此切面不共用污巾路径',21,A)
def notes(f,x,y,items,w=610):
 for i,(a,b) in enumerate(items):
  f.box(x,y+i*145,w,128,a,[b])
def new(n,title,sub,h=1150):return Fig(n,title,sub,h)
# General master sheet
f=new(2,'同一台柜：外观开口与内部位置对应','正视拆盖 + 净巾纵剖面；两图引用同一布局坐标',1260)
front(f,90,220,.49,True);side(f,695,220,.49)
notes(f,1120,210,[('上部净巾模块','H01库存位于后方，M1/M2向前送料'),('左上交付口','H07保持与释放，H08接固定口袋'),('右上电气舱','E01封闭分隔；不放在湿箱后方'),('右中回收口','R01识别 → R02受控转移'),('下部两只抽箱','R03正常；R04单件异常位')])
f.text(95,1040,'同一柜体内净污分舱；外部只有一个领巾口和一个归还口。',29,T,True)
f.text(95,1090,'图中区域是安装空间；隔板、密封、检修通道与传动护罩必须在总装CAD中落实。',26)
finish(f,'02_统一总剖面.svg','04','外观与结构共用LVT-ONE布局；净巾沿深度向前送料，右侧回收，底部正常与单件异常容器。')
# fixed front, side and top geometry
f=new(17,'统一柜体三视与开口定位','所有图统一使用W、H、D；不另造第二套柜体尺寸',1250)
front(f,160,200,.44);side(f,760,200,.44)
f.dim(160,910,600,910,'W柜宽');f.dim(95,200,95,860,'H柜高');f.dim(760,910,1068,910,'D柜深')
f.text(1250,200,'俯视：后方在上',28,T,True)
f.rect(1220,230,440,308,'#e9eef1',INK,5)
for key in ['H01','H03','H06','E01']:
 v=MODEL['modules'][key];x,y,z,w,d,h=v['box'];f.rect(1220+x*.44,230+(700-y-d)*.44,w*.44,d*.44,v['color'],INK,3);f.text(1225+x*.44,248+(700-y-d)*.44,key,20)
f.text(1250,580,'前面板／住户侧 ↓',26,T,True)
notes(f,1170,655,[('领巾口中心','x=0.36W；离底面约0.73H'),('归还口中心','x=0.74W；离底面约0.44H')],560)
f.text(95,1010,'同一正面开口投影：领巾口与H08对齐；归还口与R01对齐；底门对应R03/R04。',26)
f.text(95,1060,'归一化坐标仅锁定布局关系。W/H/D须一起校核毛巾、容量、停距与场地，再签发毫米图。',25)
finish(f,'17_整柜三视尺寸变量.svg','02','同一布局生成三视图；开口中心与内部模块投影一致，W/H/D尚未按实测冻结。')
# exploded from one model; panel and chassis same shape
f=new(15,'统一拆装图：面板移开，内部仍是同一台柜','分离展示仅为检修说明；箭头表示拆装对应，不表示实际零件飞行路径',1260)
front(f,80,235,.43,False);front(f,765,235,.43,True)
f.line(535,520,735,520,arrow=True);f.text(545,475,'移开面板',25,T)
f.line(535,790,735,790,LINE,True);f.text(560,850,'同一高度基准',22)
notes(f,1270,215,[('主服务门内','H01—H08净巾组件'),('电气检修罩内','E01与湿巾空间密封分开'),('归还口背面','R01 + R02，单独内罩'),('底部服务门内','R03与R04可分别抽出')],465)
f.text(80,1010,'补货：停发 → 授权开主门 → 仅打开净巾内罩；不得让污巾箱接触净巾托盘。',26)
f.text(80,1060,'收污：关回收入口 → 核对箱批次 → 打开底门 → 分别抽箱 → 复位、核验与对账。',26)
finish(f,'15_统一拆装爆炸.svg','04','面板轮廓、开口、下部服务门与内部模块来自同一个布局源；未用另一个外壳作为爆炸图。')
# side clean detail same master region scaled up
f=new(19,'净巾纵剖：后方分离，向前识别交付','这是同一柜体左上净巾舱的放大；公众在图右，库存位于图左',1080)
# Draw physically meaningful diagram and locator
for x,y,w,h,c in [(130,265,370,260,'#e3f0ec'),(130,540,540,48,'#6ca8a6'),(710,540,590,48,'#6a9fbf')]:f.rect(x,y,w,h,c,INK,8)
for y in [320,375,430]:f.rect(160,y,300,37,'#fff7e8',A,7)
f.rect(500,440,44,90,'#e6bd83',A,2);f.rect(670,533,40,10,'#a4bfc8',INK,1)
f.rect(1295,420,18,135,'#2a8788',T,1);f.rect(860,340,220,35,'#bfd1ed',BLUE,4)
f.rect(815,480,330,38,'#fff7e8',A,7);f.path('M1313 552L1370 660H1580V700H1330V585',INK)
f.rect(1430,620,140,36,'#fff7e8',A,4)
f.text(175,240,'H01库存 + H02底托',28,T,True);f.text(160,640,'H03 / M1',28,T);f.text(720,640,'H06 / M2保持',28,BLUE)
f.text(475,375,'H04分离',25,A);f.text(650,705,'H05过渡',25);f.text(1190,370,'H07释放件',26,T);f.text(1400,755,'H08取物斗',25,T)
f.line(210,610,540,610,arrow=True);f.line(850,610,1160,610,arrow=True)
f.dim(720,850,1290,850,'有效保持长度 ≥ 实物长度 + 停距 + 定位余量')
f.text(90,930,'先完整接住、停稳、读本条、取得ReleasePermit，再放至H08；无许可不公开交付。',26)
f.text(880,310,'局部RFID天线',26,BLUE);f.line(1300,380,1304,414,T)
finish(f,'19_送料保持出口剖面.svg','04','沿柜深后→前，与图02纵剖方向一致；禁止将整条输送线横向摆进柜宽。')
# Return section fixed two containers
f=new(26,'湿巾剖面：同柜右口入，下部独立收集','R01入口小仓 → R02分流 → R03正常箱 / R04单件异常箱',1150)
front(f,90,200,.44,True)
f.box(760,180,650,160,'R01 单条识别小仓',['外侧入口关妥后，才许可内部转移'])
f.line(1085,345,1085,400,arrow=True)
f.box(760,410,650,140,'R02 内部受控分流',['箱在位、批次与余量、路线许可一致'])
f.path('M930 555V635H790V700',T,True);f.path('M1240 555V635H1450V700',A,True)
f.box(640,710,530,175,'R03 正常回收抽箱',['核实身份与原借用轮次','实物转移成功后才提交归还'])
f.box(1220,710,530,175,'R04 单件异常抽箱',['一次仅容纳一件未知物','绑定caseId，取出前不再装入'],A)
f.text(700,975,'R04已满／分流故障：保持R01并停收；禁止混入正常箱。',25,A,True)
f.text(90,1030,'底门用于维护取箱。图中分流与通道均在同一柜体内，不能被画成外置回收副柜。',26)
finish(f,'26_湿巾回收识别分流剖面.svg','07','确定正常箱＋一个单件异常位；异常位占用时原仓保持停收，不新增第二种产品。')
# all-cabinet modules/fault/electrical/installation locator sheets
for num,name,title,ch,items,focus in [
(6,'06_统一故障位置.svg','故障位置与实物去向','04',[('H03/H04连带或卡巾','停止M1/M2，保持任务，不盲重发'),('H07许可或门位异常','保持本条，授权维护取出并对账'),('R01/R02转移不明','停收、保留回执，核实原仓与目标箱'),('R03/R04箱体异常','核箱在位、批次及容量后才恢复')],None),
(32,'32_生产模块装配拆换关系.svg','同一柜体的装配与拆换位置','12',[('1 机架与密封隔板','先建立净舱、电舱、湿舱边界'),('2 净巾组件H01—H08','轴系和后→前送料方向一起校准'),('3 回收R01—R04','与右口及底门对齐，单件异常位独立'),('4 电气与复装','上右E01入线，关罩后做互锁验收')],None),
(49,'049_04_H09_机架传动腔与检修.svg','H09 统一机架与维护界面','04',[('机架基准','同一W/H/D与两个正面开口'),('运动护罩','M1/M2轴系在左上净巾模块内'),('电气干舱','固定右上E01，禁止画成落地侧塔'),('下部箱体维护','底部门抽取R03/R04，不开启净巾罩')],None),
(62,'062_03_净污两条独立物理路径.svg','同一外壳内两条独立路径','03',[('净巾路径','后部料仓→M1→M2→H07→左上口'),('污巾路径','右下口→R01→R02→底部容器'),('隔离关系','不共用皮带、托盘、风道或接触面'),('电气与人员','E01独立干舱；维护分区并先断能')],None),
(66,'066_05_I_O逐点位置与作用.svg','同一柜体内的检测位置','05',[('S1 本条交接','H05附近；不单独证明只有一条'),('RFID / 门位','H06/H07；识别与释放反馈成对'),('S2/S3 交付证据','H08经过、有物、取走与复位'),('回收与维护输入','R01入口、R02到位、R03/R04箱位')],None),
(124,'124_17_专利标号与功能结构.svg','统一结构标号与交底位置','17',[('净巾装置','H01—H09；不得换用另一套柜形'),('回收装置','R01—R04；原位标号与剖面一致'),('电气控制','E01；许可与互锁对应实际机构'),('证据要求','位置统一不代表新颖性或效果已证实')],None),
(24,'24_RFID目标与非目标读区.svg','统一柜内RFID读区与干扰位置','06',[('净巾目标区','H06停车保持；上游H01是非目标'),('湿巾目标区','R01单件；下方R03/R04是非目标'),('天线与屏蔽','两区分别标定，不能同时随意读全柜'),('满仓与湿箱挑战','水、金属与相邻标签均需实物验证')],None)]:
 f=new(num,title,'统一模块位置；箭头或框线不构成已完成的性能、安全或专利证明',1140)
 front(f,130,210,.45,True,focus);notes(f,810,210,items,880)
 f.text(100,995,'模块编号贯穿外观、剖面、安装、I/O与交底；任何位置调整须同步修改母图和关联文件。',26,T)
 finish(f,name,ch,'引用同一产品布局；模块位置与图02、图17一致。')
# Unknown item design is now a single fixed compartment with fallback held chamber.
f=new(73,'未知湿巾：单件隔离位与原仓保持','同一台柜内的正常和异常状态，不是两款结构',1030)
f.box(110,215,490,200,'R01 识别不明',['关联returnSessionId / caseId','未确认前不结束原借用'])
f.line(605,315,725,315,arrow=True);f.box(730,215,950,200,'R04单件位空闲且取得转移许可',['转入R04；确认实物到位、原仓清空','本位锁定给一个caseId；禁止投入第二件'],A)
f.path('M355 420V625H735',A,True);f.box(740,535,940,210,'R04已占用或转移条件不满足',['物体留R01并停止接收；进入原会话待核验','物业核验、封袋编号移交 → 复位 → 对账 → 恢复'],A)
f.text(130,880,'不把多个未知湿巾混成一箱；正常收件与待核验不能显示为同一个结果。',28,T)
finish(f,'073_07_未知湿巾两种处理结构.svg','07','固定R04单件异常位；满位或故障时留在R01，停止接收并人工闭环。')
# install plan uses exactly same normalized envelope.
f=new(35,'安装俯视：一个柜体与前方维护空间','柜体坐标与图17相同；现场净距用变量标注，不能从画面估算毫米',1120)
f.rect(500,250,700,490,'#e6edf0',INK,6);f.text(705,465,'LVT-ONE 单柜',33,T,True)
f.text(710,295,'柜背 / 固定与入线',25);f.text(680,705,'住户侧 / 正面服务门',25)
f.path('M500 750H1200V995H500Z',T,False,True);f.text(615,850,'前方抽箱、开门与人员净距 C前',27,T)
f.dim(500,185,1200,185,'W');f.dim(1260,250,1260,740,'D');f.dim(1350,740,1350,995,'C前')
f.box(70,300,355,380,'现场需核对',['C后：固定与线缆','C左/C右：开门侧','C前：门扇+抽箱','通行与无障碍需求','地面、排水和防倾覆'])
f.text(500,1020,'正常箱、异常箱均从正面底门抽取；无外置副柜。',26)
finish(f,'35_安装俯视与检修尺寸.svg','15','同柜俯视与正面抽箱空间；现场检修净距与防倾覆仍须勘察和验证。')
# Local detail graphs remain valid abstractions: append shared cabinet locator, not different chassis.
for p in sorted(P.glob('04[1-8]_04_H*.svg')):
 s=(E/'局部详图原生源'/p.name).read_text(); hid=p.name.split('_')[2];match=re.search(r'height="(\d+)" viewBox="0 0 1800 (\d+)"',s)
 if not match:continue
 h=int(match[1]); f=new(0,'','',700);f.s=[]
 # New bottom band including front locator; do not alter local native detail.
 f.rect(55,h-10,1690,350,'#e9f2f4',LINE,10);front(f,100,h+10,.19,True,'H01' if hid=='H02' else 'H03' if hid in ['H04','H05'] else 'H06' if hid=='H07' else hid)
 f.text(375,h+65,f'{hid} 在同一柜体中的位置',30,T,True)
 f.text(375,h+125,'左图固定为LVT-ONE；上方为该部件的局部放大，不是另一台柜。',26)
 f.text(375,h+180,'送料方向统一：从柜后向柜前；M1、M2与H07沿柜深排列。',26)
 f.text(375,h+235,'H01—H08全部位于左上净巾舱；图02、17、19定义整柜位置。',26)
 s=s.replace(match[0],f'height="{h+365}" viewBox="0 0 1800 {h+365}"').replace('</svg>',''.join(f.s)+'</svg>')
 p.write_text(s); REG.append({'number':int(p.name[:3]),'file':p.name,'title':hid+' 局部详图与统一定位','chapter':'04','caption':'原生局部详图追加同一柜体定位；不以局部放大框作为外壳。'})
(E/'本轮结构图清单.json').write_text(json.dumps(REG,ensure_ascii=False,indent=2))
print('Generated/updated',len(REG),'technical SVG assets')
