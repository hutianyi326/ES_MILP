import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
import { excelPaths } from './simple_excel_cli.mjs';

const paths=excelPaths({source:'output/simple_20260101_p75_p25_20261103',output:'output/excel_sample/outputs/simple_model',qa:'output/simple_excel_qa/day'},'Build the fixed 2026-01-01, 50% DA four-second sample.');
const source=paths.source,output=paths.output,work=paths.qa;
const prices=JSON.parse(await fs.readFile(source+'/normalized_prices.json','utf8'));
const saved=JSON.parse(await fs.readFile(source+'/summary.json','utf8'));
const wb=Workbook.create();
const summary=wb.worksheets.add('汇总');
const inputs=wb.worksheets.add('参数');
const calc=wb.worksheets.add('4秒计算');
const raw=wb.worksheets.add('15分钟输入');
const n=21600, first=7, last=first+n-1;
const money='#,##0.00;(#,##0.00);"—"';
const precise='#,##0.000000;(#,##0.000000);"—"';
const navy='#203A5F', blue='#1D4ED8', green='#15803D', light='#EAF0F7';
for(const sh of [summary,inputs,calc,raw]){
  sh.showGridLines=false;
  sh.tabColor=sh===summary?navy:sh===inputs?'#5E7897':'#D9E2EC';
}
function base(sh,range){sh.getRange(range).format.font={name:'Arial',size:10,color:'#182433'};sh.getRange(range).format.verticalAlignment='center';}
function title(sh,text){sh.getRange('A2').values=[[text]];sh.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:navy};}
function header(sh,address){sh.getRange(address).format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',verticalAlignment:'center',rowHeight:46};}
function col(sh,letter,width){sh.getRange(`${letter}1:${letter}3`).format.columnWidth=width;}
function fmt(sh,address,format){sh.getRange(address).setNumberFormat(format);}
const deferredLinks=[];
function link(sh,address,formula){deferredLinks.push([sh,address,formula]);sh.getRange(address).format.font.color=green;}
function formulaColumn(letter,formula){calc.getRange(`${letter}${first}`).formulas=[[formula]];calc.getRange(`${letter}${first}:${letter}${last}`).fillDown();console.log('Formula column '+letter);}
base(summary,'A1:H35');base(inputs,'A1:I58');base(raw,'A1:F104');
title(summary,'西班牙储能单日收益样本');
summary.getRange('A3').values=[['2026-01-01 | Europe/Madrid | EUR | 100 MW / 200 MWh']];
summary.getRange('A5:C5').values=[['收入项目','金额（EUR）','计算口径']];header(summary,'A5:C5');
const summaryLines=[
 ['DA售电收入','AD','DA功率×4秒/3600×DA价'],
 ['DA购电支出','AE','购电记负数'],
 ['DA套利净收益','AF','售电收入＋购电支出'],
 ['aFRR Up容量收益','AG','中标MW×容量价×4/900'],
 ['aFRR Dn容量收益','AH','中标MW×容量价×4/900'],
 ['Up激活售电收入','AI','激活MW×4/3600×Up激活价'],
 ['Up潜在补能成本','AL','−Up交流售电量÷92%²×DA P25'],
 ['Dn激活购电支出','AJ','−激活MW×4/3600×Dn激活价'],
 ['Dn潜在售电价值','AN','Dn交流购电量×92%²×DA P75'],
 ['Up电量净收益','AO','Up收入＋补能成本（小计）'],
 ['Dn电量净收益','AP','Dn购电支出＋售电价值（小计）'],
 ['总收益（包含估值）','AQ','DA净收益＋双向容量＋双向电量净收益'],
];
summaryLines.forEach(([label,c,description],i)=>{let r=6+i;summary.getRange(`A${r}:C${r}`).values=[[label,null,description]];link(summary,`B${r}`,`=SUM('4秒计算'!${c}${first}:${c}${last})`);});
fmt(summary,'B6:B17',money);summary.getRange('A17:C17').format.fill=light;summary.getRange('A17:C17').format.font.bold=true;
summary.getRange('A20:B20').values=[['数据与价格基准','数值']];header(summary,'A20:B20');
const metrics=[['DA P25（EUR/MWh）',"='参数'!B23"],['DA P75（EUR/MWh）',"='参数'!B24"],['Up激活价格有价覆盖率',`=SUM('4秒计算'!AS${first}:AS${last})/${n}`],['Dn激活价格有价覆盖率',`=SUM('4秒计算'!AT${first}:AT${last})/${n}`],['Up激活交流电量（MWh）',`=SUM('4秒计算'!AB${first}:AB${last})*'参数'!B20/'参数'!B22`],['Dn激活交流电量（MWh）',`=SUM('4秒计算'!AC${first}:AC${last})*'参数'!B20/'参数'!B22`]];
metrics.forEach(([a,f],i)=>{summary.getRange(`A${21+i}`).values=[[a]];link(summary,`B${21+i}`,f);});
fmt(summary,'B21:B26',money);fmt(summary,'B23:B24','0.00%');
summary.getRange('A29').values=[['范围：激活无价格时段不补零；汇总为有价时段计算合计。']];
summary.getRange('A30').values=[['估值：Dn以当日P75售电、Up以P25补能，均计两次92%效率；不安排真实后续调度。']];
summary.getRange('A31').values=[['简化：aFRR不限制SOC；DA采用已选定的一次先充后放窗口；不含税费及退化成本。']];
summary.getRange('A33').values=[['查看“4秒计算”：每行一个4秒；按Ctrl+`切换显示Excel公式；“参数”右侧有列公式说明。']];
for(const c of ['A','B','C'])col(summary,c,c==='A'?32:c==='B'?22:55);

title(inputs,'参数与公式说明');
inputs.getRange('A3').values=[['蓝字黄底为参数；绿色为跨表取数；黑色为本表公式。']];
inputs.getRange('A5:C5').values=[['参数','数值','单位／说明']];header(inputs,'A5:C5');
const paramRows={6:['交流侧功率',100,'MW'],7:['直流侧电量',200,'MWh'],8:['DA参与比例',.5,'%'],9:['aFRR参与比例',null,'1−DA比例'],10:['充电效率',.92,'%'],11:['放电效率',.92,'%'],12:['DA分配功率',null,'MW'],13:['DA分配电量',null,'MWh'],14:['aFRR Up申报功率',null,'MW'],15:['aFRR Dn申报功率',null,'MW'],16:['Up容量报价',1,'EUR/MW/15分钟'],17:['Dn容量报价',1,'EUR/MW/15分钟'],18:['Up激活价差阈值',200,'EUR/MWh，Up价−同时段DA价'],19:['Dn激活价差阈值',0,'EUR/MWh，同时段DA价−Dn价'],20:['明细时间步长',4,'秒'],21:['容量价格对应时长',900,'秒（15分钟）'],22:['每小时秒数',3600,'秒'],23:['当日DA P25',null,'EUR/MWh，线性百分位'],24:['当日DA P75',null,'EUR/MWh，线性百分位'],25:['单价分位P25',.25,'%'],26:['单价分位P75',.75,'%']};
for(const [r,v]of Object.entries(paramRows))inputs.getRange(`A${r}:C${r}`).values=[v];
for(const r of [6,7,8,10,11,16,17,18,19]){inputs.getRange(`B${r}`).format.fill='#FFF3CC';inputs.getRange(`B${r}`).format.font.color=blue;}
for(const [r,f]of [[9,'=1-B8'],[12,'=B6*B8'],[13,'=B7*B8'],[14,'=B6*B9'],[15,'=B6*B9'],[23,"=PERCENTILE('15分钟输入'!$B$7:$B$102,B25)"],[24,"=PERCENTILE('15分钟输入'!$B$7:$B$102,B26)"]])inputs.getRange(`B${r}`).formulas=[[f]];
fmt(inputs,'B6:B26',money);for(const r of [8,9,10,11,25,26])fmt(inputs,`B${r}`,'0.0%');
inputs.getRange('A49').values=[['口径与来源']];inputs.getRange('A49').format.font.bold=true;
const notes=[
 '价格：ENTSO-E官方API；抓取日期2026-11-03，样本日2026-01-01，西班牙当地日。',
 '端点 https://web-api.tp.entsoe.eu/api；西班牙区域 10YES-REE------0。',
 'DA：A44，A01日前序列；容量：A81/B95/A51，日合同A01；激活：A84/A96/A67/A01。',
 '15分钟价格映射到225个4秒行；容量收入按4/900均摊，禁止每4秒重复全额计费。',
 '激活数据A03曲线按有效区间展开；没有价格的原始点保持空缺；有效零价保留为0。',
 '容量出清价严格大于报价才中标；激活价差严格大于阈值才触发。',
 'P25/P75基于96个15分钟DA价格等权、含重复值、线性插值；非高低四分位均价。',
 'Dn可售量=购电量×充电效率×放电效率；Up补能量=售电量÷放电效率÷充电效率。',
 'aFRR不限制SOC；双方向独立筛选；无价时段的激活收益留空，行总额仅汇总可计算部分。',
 'DA窗口取已有非MILP日内搜索；充电10:30—12:45、放电20:00—22:00，尾段部分功率。',
 'DA窗口形状固定，修改阈值/效率/P25/P75会重算现金流；不会自动重新搜索DA调度。',
 '修改MW/MWh或DA比例后，DA功率按比例缩放；容量与时长可行性须重新运行窗口搜索。',
 'P75售电和P25补能均为估值，不保证发生在激活之后，亦不校验后续功率/电量可行性。',
 '原始请求和SHA256随计算存档；本工作簿保留原生价格及15分钟输入，未包含任何API凭据。',
];
notes.forEach((v,i)=>inputs.getRange(`A${50+i}`).values=[[v]]);
col(inputs,'A',32);col(inputs,'B',19);col(inputs,'C',43);col(inputs,'D',3);col(inputs,'E',24);col(inputs,'F',115);
inputs.getRange('E5:F5').values=[['4秒计算列','首行公式／解释']];header(inputs,'E5:F5');

title(raw,'15分钟原始价格与DA窗口');
raw.getRange('A3').values=[['DA与容量：ENTSO-E；DA窗口功率比例：既有非MILP搜索结果。']];
raw.getRange('A6:F6').values=[['开始时间 CET','DA价格 EUR/MWh','Up容量价 EUR/MW/15min','Dn容量价 EUR/MW/15min','DA充电功率比例','DA放电功率比例']];header(raw,'A6:F6');
const daySerial=Date.UTC(2026,0,1)/86400000+25569;
raw.getRange('A7:F102').values=Array.from({length:96},(_,q)=>[daySerial+q/96,prices.da[q],prices.capacity.up[q],prices.capacity.down[q],saved.da.charge_mwh_ac[q]/.25/50,saved.da.discharge_mwh_ac[q]/.25/50]);
fmt(raw,'A7:A102','yyyy-mm-dd hh:mm');fmt(raw,'B7:D102',money);fmt(raw,'E7:F102','0.0000%');
raw.getRange('B7:F102').format.font.color=blue;
raw.freezePanes.freezeRows(6);for(const c of ['A','B','C','D','E','F'])col(raw,c,c==='A'?23:22);

console.log('Small sheets prepared');
title(calc,'4秒逐行价格、参数与收益');
calc.getRange('A3').values=[['CET；金额EUR；无激活价保留空白；容量收入按225个4秒均摊；详细列公式见“参数”。']];
const headings=['序号','开始时间 CET','结束时间 CET','15分钟序号','时长 秒','DA价格 EUR/MWh','Up容量价 EUR/MW/15min','Dn容量价 EUR/MW/15min','Up激活价 EUR/MWh','Dn激活价 EUR/MWh','DA参与比例','DA功率 MW','DA电量 MWh','Up申报 MW','Dn申报 MW','Up容量报价 EUR/MW/15min','Dn容量报价 EUR/MW/15min','Up激活阈值 EUR/MWh','Dn激活阈值 EUR/MWh','充电效率','放电效率','DA P25 EUR/MWh','DA P75 EUR/MWh','DA充电 MW','DA放电 MW','Up中标 MW','Dn中标 MW','Up激活 MW','Dn激活 MW','DA售电收入 EUR','DA购电支出 EUR','DA净收益 EUR','Up容量收益 EUR','Dn容量收益 EUR','Up激活收入 EUR','Dn激活支出 EUR','Up补能电量 MWh','Up补能支出 EUR','Dn可售电量 MWh','Dn售电估值 EUR','Up电量净收益 EUR','Dn电量净收益 EUR','本行合计 EUR','累计合计 EUR','Up有价 1/0','Dn有价 1/0'];
headings[43]='时长 小时';
calc.getRange('A6:AT6').values=[headings];header(calc,'A6:AT6');
// Write sparse factual inputs once; all business calculations below are Excel formulas.
for(let offset=0;offset<n;offset+=1800){
 const count=Math.min(1800,n-offset);
 const rows=Array.from({length:count},(_,j)=>{const i=offset+j;return [i+1,daySerial+i/21600,daySerial+(i+1)/21600,Math.floor(i/225)+1];});
 calc.getRangeByIndexes(first-1+offset,0,count,4).values=rows;
 calc.getRangeByIndexes(first-1+offset,8,count,2).values=Array.from({length:count},(_,j)=>[prices.activation.up[offset+j],prices.activation.down[offset+j]]);
 console.log('Input rows '+(offset+count));
}
const f={E:"='参数'!$B$20",F:`=INDEX('15分钟输入'!$B$7:$B$102,D${first})`,G:`=INDEX('15分钟输入'!$C$7:$C$102,D${first})`,H:`=INDEX('15分钟输入'!$D$7:$D$102,D${first})`,K:"='参数'!$B$8",L:"='参数'!$B$12",M:"='参数'!$B$13",N:"='参数'!$B$14",O:"='参数'!$B$15",P:"='参数'!$B$16",Q:"='参数'!$B$17",R:"='参数'!$B$18",S:"='参数'!$B$19",T:"='参数'!$B$10",U:"='参数'!$B$11",V:"='参数'!$B$23",W:"='参数'!$B$24",X:`=L${first}*INDEX('15分钟输入'!$E$7:$E$102,D${first})`,Y:`=L${first}*INDEX('15分钟输入'!$F$7:$F$102,D${first})`,Z:`=IF(G${first}>P${first},N${first},0)`,AA:`=IF(H${first}>Q${first},O${first},0)`,AB:`=IF(ISNUMBER(I${first}),IF(AND(Z${first}>0,I${first}-F${first}>R${first}),Z${first},0),"")`,AC:`=IF(ISNUMBER(J${first}),IF(AND(AA${first}>0,F${first}-J${first}>S${first}),AA${first},0),"")`,AD:`=Y${first}*E${first}/'参数'!$B$22*F${first}`,AE:`=-X${first}*E${first}/'参数'!$B$22*F${first}`,AF:`=SUM(AD${first}:AE${first})`,AG:`=Z${first}*G${first}*E${first}/'参数'!$B$21`,AH:`=AA${first}*H${first}*E${first}/'参数'!$B$21`,AI:`=IF(ISNUMBER(AB${first}),AB${first}*E${first}/'参数'!$B$22*I${first},"")`,AJ:`=IF(ISNUMBER(AC${first}),-AC${first}*E${first}/'参数'!$B$22*J${first},"")`,AK:`=IF(ISNUMBER(AB${first}),AB${first}*E${first}/'参数'!$B$22/U${first}/T${first},"")`,AL:`=IF(ISNUMBER(AK${first}),-AK${first}*V${first},"")`,AM:`=IF(ISNUMBER(AC${first}),AC${first}*E${first}/'参数'!$B$22*T${first}*U${first},"")`,AN:`=IF(ISNUMBER(AM${first}),AM${first}*W${first},"")`,AO:`=IF(ISNUMBER(AB${first}),SUM(AI${first},AL${first}),"")`,AP:`=IF(ISNUMBER(AC${first}),SUM(AJ${first},AN${first}),"")`,AQ:`=SUM(AF${first},AG${first},AH${first},AO${first},AP${first})`,AS:`=IF(ISNUMBER(I${first}),1,0)`,AT:`=IF(ISNUMBER(J${first}),1,0)`};
for(const [c,formula]of Object.entries(f))formulaColumn(c,formula);
formulaColumn('AR',`=E${first}/'参数'!$B$22`);
let gr=6;for(const [c,formula]of Object.entries(f)){inputs.getRange(`E${gr}:F${gr}`).values=[[`${c} ${headings[(function(s){let n=0;for(const x of s)n=n*26+x.charCodeAt(0)-64;return n-1;})(c)]}`,"'"+formula]];gr++;}
inputs.getRange(`E${gr}:F${gr}`).values=[['AR 时长小时',"'=E7/'参数'!$B$22"]];
inputs.getRange('F6:F47').format.font={name:'Arial',size:10,color:'#182433'};
console.log('Formatting detailed sheet');
base(calc,`A6:AT${last}`);
header(calc,'A6:AT6');
calc.getRange(`F7:J${last}`).format.font.color=green;calc.getRange(`I7:J${last}`).format.font.color=blue;calc.getRange(`K7:W${last}`).format.font.color=green;
fmt(calc,`B7:C${last}`,'yyyy-mm-dd hh:mm:ss');fmt(calc,`F7:W${last}`,money);for(const c of ['K','T','U'])fmt(calc,`${c}7:${c}${last}`,'0.0%');
fmt(calc,`X7:AC${last}`,money);fmt(calc,`AD7:AR${last}`,precise);fmt(calc,`AS7:AT${last}`,'0');
for(let c=0;c<46;c++)calc.getRangeByIndexes(0,c,3,1).format.columnWidth=(c===1||c===2)?24:c===0||c===3||c===4?9:17;
calc.getRange(`AQ6:AR${last}`).format.fill='#EAF0F7';header(calc,'AQ6:AR6');
calc.freezePanes.freezeRows(6);calc.freezePanes.freezeColumns(3);
calc.tables.add(`A6:AT${last}`,true,'FourSecondSample');
console.log('All rows and formulas authored');
for(const [sh,address,formula]of deferredLinks)sh.getRange(address).formulas=[[formula]];
wb.recalculate();
console.log('Recalculation complete');
const svals=summary.getRange('B6:B17').values.map(r=>r[0]);
const expected=[saved.da.discharge_income_eur,-saved.da.charge_cost_eur,saved.da.profit_eur,saved.afrr.up.capacity_eur,saved.afrr.down.capacity_eur,saved.afrr.up.cash_eur,saved.afrr.up.da_restoration_cash_eur,saved.afrr.down.cash_eur,saved.afrr.down.da_restoration_cash_eur,saved.afrr.up.efficiency_adjusted_reference_eur,saved.afrr.down.efficiency_adjusted_reference_eur,saved.total_revenue_eur];
const comparisons=svals.map((v,i)=>({row:i+6,value:v,expected:expected[i],difference:typeof v==='number'?v-expected[i]:null}));
console.log(JSON.stringify({comparisons}));
if(comparisons.some(x=>typeof x.value!=='number'||Math.abs(x.difference)>1e-5))throw new Error('Workbook summary reconciliation failed');
const p25=inputs.getRange('B23').values[0][0],p75=inputs.getRange('B24').values[0][0];
if(Math.abs(p25-64.72)>1e-8||Math.abs(p75-102.22)>1e-8)throw new Error('Percentile mismatch');
// Change a live threshold and verify the native formula graph responds, then restore it.
const baseDn=summary.getRange('B16').values[0][0];
inputs.getRange('B19').values=[[1000]];
wb.recalculate();
const noDn=summary.getRange('B16').values[0][0];
if(noDn!==0)throw new Error('Threshold recalculation failed');
inputs.getRange('B19').values=[[0]];wb.recalculate();
if(Math.abs(summary.getRange('B16').values[0][0]-baseDn)>1e-6)throw new Error('Input restoration failed');
const inspections=[];
for(const [sheet,range]of [['汇总','A5:C17'],['参数','A16:C26'],['4秒计算','Z7:AP9'],['4秒计算',`AQ${last-1}:AT${last}`],['15分钟输入','A7:F10']]){
 const result=await wb.inspect({kind:'table',range:`'${sheet}'!${range}`,include:'values,formulas',tableMaxRows:13,tableMaxCols:8,maxChars:2400});inspections.push(result.ndjson);
}
await fs.mkdir(output,{recursive:true});
await fs.writeFile(work+'/verification.json',JSON.stringify({comparisons,p25,p75,thresholdTest:{baseDn,noDn},inspections},null,2));
for(const [sheet,range,key]of [['汇总','A1:C27','summary'],['参数','A5:C26','parameters'],['4秒计算','F6:J12','prices'],['4秒计算','AD6:AQ12','revenues'],['15分钟输入','A5:F13','sources']]){
 const png=await wb.render({sheetName:sheet,range,scale:1.4,format:'png'});
 await fs.writeFile(work+`/${key}.png`,new Uint8Array(await png.arrayBuffer()));
}
console.log('Visual previews rendered');
const file=await SpreadsheetFile.exportXlsx(wb);
const filename=output+'/西班牙_20260101_4秒收益计算样本.xlsx';
await file.save(filename);
console.log(JSON.stringify({output:filename,total:summary.getRange('B17').values[0][0]}));
