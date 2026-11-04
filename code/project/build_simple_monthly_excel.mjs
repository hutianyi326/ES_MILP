import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
import { excelPaths } from './simple_excel_cli.mjs';

const paths=excelPaths({source:'output/simple_period_20250601_20261031_20261103',output:'output/excel_monthly/outputs/simple_model',qa:'output/simple_excel_qa/monthly'},'Build the fixed 17-month, three-allocation workbook.');
const dataDir=paths.source,outputDir=paths.output,work=paths.qa;
const data=JSON.parse(await fs.readFile(dataDir+'/results.json','utf8'));
const wb=Workbook.create();
const summary=wb.worksheets.add('月度收益');
const params=wb.worksheets.add('参数与口径');
const calc=wb.worksheets.add('逐日计算');
const source=wb.worksheets.add('每日计算依据');
const navy='#203A5F', light='#EDF2F7', blue='#1D4ED8', green='#15803D', ink='#182433';
const money='#,##0.00;(#,##0.00);"—"';
const num='#,##0.0000;(#,##0.0000);"—"';
const integer='#,##0;(#,##0);"—"';
const percent='0.0%;(0.0%);"—"';
const scenarios=data.configuration.scenarios;
const nd=data.daily_inputs.length, first=7, srcLast=first+nd-1, last=first+data.daily_scenarios.length-1;
const serial=s=>Date.parse(s+'T00:00:00Z')/86400000+25569;
const monthSerial=s=>serial(s+'-01');
const deferred=[];
function base(sh,range){sh.showGridLines=false;sh.getRange(range).format={font:{name:'Arial',size:10,color:ink},verticalAlignment:'center',rowHeight:22};}
function col(sh,c,width){sh.getRange(`${c}1:${c}3`).format.columnWidth=width;}
function title(sh,t){sh.getRange('A2').values=[[t]];sh.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:navy};}
function header(sh,r){sh.getRange(r).format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,rowHeight:45};}
function fmt(sh,r,f){sh.getRange(r).setNumberFormat(f);}
function seed(sh,c,f,end=last){sh.getRange(`${c}${first}`).formulas=[[f]];sh.getRange(`${c}${first}:${c}${end}`).fillDown();}
function sumCase(c,id,monthCell){let f=`SUMIFS('逐日计算'!$${c}$7:$${c}$${last},'逐日计算'!$A$7:$A$${last},${id}`;if(monthCell)f+=`,'逐日计算'!$D$7:$D$${last},${monthCell}`;return f+')';}

base(summary,'A1:N82');base(params,'A1:F72');base(calc,`A1:AG${last}`);base(source,`A1:AB${srcLast}`);
summary.tabColor=navy;params.tabColor='#68839E';source.tabColor='#D5C8B4';
title(summary,'西班牙储能月度收益对比');
summary.getRange('A3').values=[['2025-06-01至2026-10-31，518天。100 MW / 200 MWh。全部金额为EUR，支出记负数。']];
summary.getRange('A3').format.font.italic=true;
summary.getRange('A5:N5').values=[['DA比例','DA净收益','Up容量收益','Dn容量收益','Up激活收入','Dn激活收支','Dn后续售电价值','Up潜在补能收支','aFRR电量净额','当期收支合计','含估值总收益','激活Up有价率','激活Dn有价率','覆盖天数']];header(summary,'A5:N5');
for(let i=0;i<3;i++){
  let r=6+i,id=i+1;
  deferred.push(()=>{
    summary.getRange(`A${r}`).formulas=[[`='参数与口径'!C${22+i}`]];
    const cols={B:'K',C:'L',D:'M',E:'Q',F:'R',G:'X',H:'Y',I:'Z',J:'AA',K:'AB'};
    for(const [dest,orig]of Object.entries(cols))summary.getRange(`${dest}${r}`).formulas=[['='+sumCase(orig,id)]];
    summary.getRange(`L${r}`).formulas=[['='+sumCase('AF',id)+'/'+sumCase('AE',id)]];
    summary.getRange(`M${r}`).formulas=[['='+sumCase('AG',id)+'/'+sumCase('AE',id)]];
    summary.getRange(`N${r}`).values=[[nd]];
  });
}
fmt(summary,'A6:A8',percent);fmt(summary,'B6:K8',money);fmt(summary,'L6:M8','0.00%');fmt(summary,'N6:N8',integer);
summary.getRange('J6:K8').format.fill=light;summary.getRange('K6:K8').format.font.bold=true;
summary.getRange('A10').values=[['含估值总收益＝DA净收益＋Up/Dn容量＋Up/Dn激活收支＋Dn后续售电价值＋Up潜在补能收支。']];
summary.getRange('A11').values=[['后续售电、补能是估值，计入各激活发生月；当期收支合计不含这两项。负DA价格下，补能收支可能为正。']];
summary.getRange('A12').values=[['aFRR不约束SOC，上下调独立筛选；无激活价时段不补零，月度金额为可计算部分合计。DA为事后已知价格下的窗口搜索。']];
summary.getRange('A13').values=[['2025年6—9月DA原生为小时产品，在原交付小时内映射至15分钟。三个比例均按MW与MWh同比例分配。']];
for(const r of [10,11,12,13])summary.getRange(`A${r}`).format.font={name:'Arial',size:10,color:'#526277'};
summary.getRange('A16:N16').values=[['DA比例','月份','DA净收益','Up容量收益','Dn容量收益','Up激活收入','Dn激活收支','Dn后续售电价值','Up潜在补能收支','aFRR电量净额','当期收支合计','含估值总收益','Up有价率','Dn有价率']];header(summary,'A16:N16');
const months=[...new Set(data.monthly.map(r=>r.month))];
for(let i=0;i<data.monthly.length;i++){
  const item=data.monthly[i],r=17+i,id=scenarios.findIndex(s=>s.label===item.scenario)+1;
  summary.getRange(`B${r}`).values=[[monthSerial(item.month)]];
  deferred.push(()=>{
    summary.getRange(`A${r}`).formulas=[[`='参数与口径'!C${21+id}`]];
    for(const [dest,orig]of Object.entries({C:'K',D:'L',E:'M',F:'Q',G:'R',H:'X',I:'Y',J:'Z',K:'AA',L:'AB'}))
      summary.getRange(`${dest}${r}`).formulas=[['='+sumCase(orig,id,`$B${r}`)]];
    summary.getRange(`M${r}`).formulas=[['='+sumCase('AF',id,`$B${r}`)+'/'+sumCase('AE',id,`$B${r}`)]];
    summary.getRange(`N${r}`).formulas=[['='+sumCase('AG',id,`$B${r}`)+'/'+sumCase('AE',id,`$B${r}`)]];
  });
  if(i===0||i===17||i===34)summary.getRange(`A${r}:N${r}`).format.borders={top:{style:'medium',color:'#7C91A8'}};
}
fmt(summary,'A17:A67',percent);fmt(summary,'B17:B67','yyyy-mm');fmt(summary,'C17:L67',money);fmt(summary,'M17:N67','0.00%');
summary.getRange('L17:L67').format.fill=light;summary.getRange('L17:L67').format.font.bold=true;
summary.tables.add('A16:N67',true,'MonthlyComparison');
summary.freezePanes.freezeRows(16);summary.freezePanes.freezeColumns(2);
col(summary,'A',12);col(summary,'B',20);for(const c of ['C','D','E','F','G','H','I','J','K','L'])col(summary,c,21);col(summary,'M',14);col(summary,'N',14);

// Use the same visible monthly comparison as the chart source; reserve the chart area below the table.
summary.getRange('A70:D70').values=[['月份','100% DA','50% DA','80% DA']];header(summary,'A70:D70');
for(let m=0;m<17;m++){
  const r=71+m;summary.getRange(`A${r}`).values=[[months[m]]];
  deferred.push(()=>{for(let s=0;s<3;s++)summary.getRangeByIndexes(r-1,s+1,1,1).formulas=[[`=L${17+s*17+m}`]];});
}
fmt(summary,'B71:D87',money);
const chart=summary.charts.add('line',summary.getRange('A70:D87'));
chart.setPosition('F70','N89');chart.title='月度含估值总收益（EUR）';
chart.titleTextStyle.fontSize=13;chart.titleTextStyle.typeface='Arial';
chart.legend={position:'top',textStyle:{typeface:'Arial',fontSize:11}};
chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};
chart.yAxis={numberFormatCode:'#,##0,,"M"',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:11}};
chart.yAxis.title.text='EUR 百万';
for(const [i,c]of ['#203A5F','#B55D34','#3D8470'].entries()){chart.series.items[i].fill=c;chart.series.items[i].line={fill:c,style:'solid',width:2};}

title(params,'参数与计算口径');
params.getRange('A3').values=[['本次报价、阈值和效率已用于逐4秒筛选。仅三个DA比例为可修改项；改动其他参数需要重新运行计算。']];
params.getRange('A5:C5').values=[['固定参数','数值','单位及含义']];header(params,'A5:C5');
const driverRows={6:['交流侧功率',100,'MW'],7:['直流侧额定电量',200,'MWh'],8:['单向效率',.92,'充电、放电分别92%'],9:['Up容量报价',1,'EUR/MW/15分钟'],10:['Dn容量报价',1,'EUR/MW/15分钟'],11:['Up激活价差阈值',200,'EUR/MWh，Up价减同时段DA价'],12:['Dn激活价差阈值',0,'EUR/MWh，同时段DA价减Dn价'],13:['激活步长',4,'秒'],14:['一小时',3600,'秒'],15:['容量价格对应时长',900,'秒'],16:['Up补能DA分位',.25,'每日P25，线性插值'],17:['Dn后续售电DA分位',.75,'每日P75，线性插值']};
for(const [r,v]of Object.entries(driverRows))params.getRange(`A${r}:C${r}`).values=[v];
fmt(params,'B6:B17',num);for(const r of [8,16,17])fmt(params,`B${r}`,percent);
params.getRange('B6:B17').format.fill=light;
params.getRange('A19').values=[['蓝字黄底为可修改DA比例。所有日度计算共用同一组固定价格筛选结果，再按DA/aFRR分配功率缩放。']];
params.getRange('A21:F21').values=[['编号','策略名称','DA比例','DA功率 MW','DA电量 MWh','aFRR各方向 MW']];header(params,'A21:F21');
scenarios.forEach((s,i)=>{
  let r=22+i;params.getRange(`A${r}:C${r}`).values=[[i+1,s.label,s.da_share]];
  params.getRange(`D${r}:F${r}`).formulas=[[`=$B$6*C${r}`,`=$B$7*C${r}`,`=$B$6*(1-C${r})`]];
});
fmt(params,'C22:C24',percent);fmt(params,'D22:F24',money);params.getRange('C22:C24').format.fill='#FFF3CC';params.getRange('C22:C24').format.font.color=blue;
params.dataValidations.add({range:'C22:C24',rule:{type:'decimal',operator:'between',formula1:0,formula2:1}});
params.getRange('A27').values=[['计算方法与边界']];params.getRange('A27').format.font.bold=true;
const notes=[
 'DA：每日一次连续充电，完成后再连续放电；15分钟起点；最后一段可为部分功率；电量深度按1%搜索。',
 'DA：每日初末可用直流电量为0，不加SOC缓冲。选择非负最大净收益；属于已知当日价格的事后搜索。',
 'DA：100%配置先计算每日窗口。功率和电量同步缩放，窗口及深度不变，因此可精确复用到50%和80%。',
 '容量：Up、Dn各申报未参加DA的全部功率；出清价严格高于1才全额中标。收益＝中标MW×EUR/MW/15分钟。',
 '激活：Up价−同时段DA＞200，或同时段DA−Dn价＞0。逐4秒以对应已中标MW激活，未中标不计激活。',
 'Up激活收支＝交流售电MWh×Up价；Dn激活收支＝−交流购电MWh×Dn价。保留负价原符号。',
 'Dn后续可售MWh＝Dn交流购电MWh×92%×92%；估值单价为当日DA的P75。',
 'Up补能MWh＝Up交流售电MWh÷92%÷92%；补能收支＝−补能MWh×当日DA的P25。',
 'P25/P75采用当地日全部15分钟价格等权，含重复值；排序位置为(n−1)×分位并线性插值。',
 '售电与补能均为潜在估值，计入激活发生日/月；没有安排真实后续交易，也不保证价格出现在激活之后。',
 'aFRR不限制SOC、持续能量或后续补能功率；Up/Dn独立筛选，不执行同一电站方向互斥。',
 '数据为系统价格，不是本站实际调节指令。空值不推断为未激活；金额只汇总有价格且满足条件的部分。',
 '有价率＝该方向有效4秒价格点数÷全月4秒点数，按真实时长加权；不是中标率或激活率。',
 '100% DA场景aFRR申报为0，各aFRR金额为0；有价率仍显示公共市场数据覆盖率。',
 '跨日和夏令时按Europe/Madrid交付日分组。包含23小时与25小时日，不假设每天固定96个15分钟。',
 '2025年6—9月DA原生小时价只在其原交付小时内映射；不视为四个独立15分钟出清价。',
 '未扣税费、网络费、交易费、退化、投资和运营成本。当前模型输出为简化毛收益与电量估值。',
 '“每日计算依据”的已筛选每MW价格积分来自4秒原价；报价、阈值或效率变更需要重新生成依据。',
 '改DA比例可直接重算全部金额。更改策略名称后同时更新“策略名称”单元格；报价、阈值保持本次固定值。'
];
notes.forEach((t,i)=>params.getRange(`A${28+i}`).values=[[t]]);
params.getRange('A49').values=[['数据来源与追溯']];params.getRange('A49').format.font.bold=true;
const sources=[
 '整理快照：2026-11-03；518日，49,732个15分钟、11,189,700个4秒；所有DA与容量价格齐全。',
 'ENTSO-E生产API：https://web-api.tp.entsoe.eu/api；区域：10YES-REE------0。',
 'DA补抓：A44/A01；aFRR容量补抓：A81/B95/A51/日合同A01；4秒激活：A84/A67/A96/A01，A08 CBMP。',
 '前期归档DA：OMIE官方文件 https://www.omie.es/en/file-download 。容量：REE/eSIOS官方接口 https://api.esios.ree.es/ 。',
 'A03原生有效区间与显式空值按源文件保留：https://transparencyplatform.zendesk.com/hc/en-us/articles/30262342482961-CurveType-A01-vs-CurveType-A03 。',
 '日度与15分钟计算依据、逐日场景CSV、来源文件SHA256及验证记录与本次结果一并存档。',
 '规则事实：价格频率、单位、时间与空值来自官方归档。建模假设：上述分配、触发、调度和估值口径由本次简化方案确定。'
];
sources.forEach((t,i)=>params.getRange(`A${50+i}`).values=[[t]]);
col(params,'A',31);col(params,'B',23);col(params,'C',43);col(params,'D',21);col(params,'E',21);col(params,'F',23);

title(source,'每日计算依据');
source.getRange('A3').values=[['完整配置DA窗口及固定报价/阈值下的aFRR每MW积分。空激活价不补零；W—Z在该方向全天无价格时留空。']];
source.getRange('A4').values=[['来源：2026-11-03整理的官方OMIE、REE/eSIOS、ENTSO-E数据；价格口径和原始记录见“参数与口径”。']];
const sourceHeaders=['当地交付日','月份','15分钟点数','实际小时','DA P25 EUR/MWh','DA P75 EUR/MWh','DA购电 MWh 全配置','DA售电 MWh 全配置','DA购电收支 EUR 全配置','DA售电收入 EUR 全配置','DA循环深度','充电开始 含偏移','放电开始 含偏移','Up中标价格和 EUR/MW','Dn中标价格和 EUR/MW','Up中标15分钟数','Dn中标15分钟数','Up有价4秒数','Dn有价4秒数','全日4秒数','Up触发4秒数 每MW','Dn触发4秒数 每MW','Up激活 MWh/MW','Dn激活 MWh/MW','Up激活现金 EUR/MW','Dn激活现金 EUR/MW','Up有价率','Dn有价率'];
source.getRange('A6:AB6').values=[sourceHeaders];header(source,'A6:AB6');
const sourceRows=data.daily_inputs.map(d=>[serial(d.date),monthSerial(d.month),d.qh_count,null,d.da_p25,d.da_p75,d.da_buy_full_mwh,d.da_sell_full_mwh,d.da_purchases_full_eur,d.da_sales_full_eur,d.da_cycle_depth,d.charge_start,d.discharge_start,d.capacity_up_per_mw,d.capacity_down_per_mw,d.capacity_up_awarded_qh,d.capacity_down_awarded_qh,d.up_valid_points,d.down_valid_points,d.expected_points,d.up_active_points,d.down_active_points,null,null,d.up_valid_points?d.up_cash_per_mw:null,d.down_valid_points?d.down_cash_per_mw:null,null,null]);
source.getRange(`A7:AB${srcLast}`).values=sourceRows;
seed(source,'D','=C7/4',srcLast);
seed(source,'W',`=IF(R7>0,U7*'参数与口径'!$B$13/'参数与口径'!$B$14,"")`,srcLast);
seed(source,'X',`=IF(S7>0,V7*'参数与口径'!$B$13/'参数与口径'!$B$14,"")`,srcLast);
seed(source,'AA','=R7/T7',srcLast);seed(source,'AB','=S7/T7',srcLast);
fmt(source,`A7:A${srcLast}`,'yyyy-mm-dd');fmt(source,`B7:B${srcLast}`,'yyyy-mm');fmt(source,`C7:D${srcLast}`,integer);fmt(source,`E7:J${srcLast}`,num);fmt(source,`K7:K${srcLast}`,percent);fmt(source,`N7:O${srcLast}`,num);fmt(source,`P7:V${srcLast}`,integer);fmt(source,`W7:Z${srcLast}`,num);fmt(source,`AA7:AB${srcLast}`,'0.00%');
for(let i=0;i<28;i++)source.getRangeByIndexes(0,i,3,1).format.columnWidth=[0,1].includes(i)?15:[11,12].includes(i)?30:19;
source.tables.add(`A6:AB${srcLast}`,true,'DailyCalculationBasis');source.freezePanes.freezeRows(6);source.freezePanes.freezeColumns(2);

title(calc,'逐日分配与收益计算');
calc.getRange('A3').values=[['三种策略共用日度价格积分，按分配功率与电量分别计算。金额EUR，电量MWh，功率MW。']];
calc.getRange('A4').values=[['无价日的对应激活项目保持空白；合计只包含可计算金额。市场有价率用于核对数据覆盖，不是本站调节时长。']];
const calcHeaders=['策略编号','策略名称','交付日','月份','DA比例','DA功率 MW','DA电量 MWh','aFRR各方向 MW','DA售电收入','DA购电收支','DA净收益','Up容量收益','Dn容量收益','容量收益小计','Up激活交流MWh','Dn激活交流MWh','Up激活收入','Dn激活收支','激活收支小计','当日DA P25','当日DA P75','Dn后续可售MWh','Up补能MWh','Dn后续售电价值','Up潜在补能收支','aFRR电量净额','当期收支合计','含估值总收益','Up有价率','Dn有价率','全日4秒数','Up有价4秒数','Dn有价4秒数'];
calc.getRange('A6:AG6').values=[calcHeaders];header(calc,'A6:AG6');
calc.getRange(`A7:A${last}`).values=data.daily_scenarios.map(x=>[scenarios.findIndex(s=>s.label===x.scenario)+1]);
// One table, one scalar calculation pattern; scenario rows differ only by the allocation driver.
for(let s=0;s<3;s++){
  const begin=7+s*nd,end=begin+nd-1;
  for(const [dest,src]of Object.entries({C:'A',D:'B',T:'E',U:'F',AC:'AA',AD:'AB',AE:'T',AF:'R',AG:'S'})){
    calc.getRange(`${dest}${begin}`).formulas=[[`='每日计算依据'!${src}7`]];
    calc.getRange(`${dest}${begin}:${dest}${end}`).fillDown();
  }
  for(const [dest,f]of Object.entries({I:`='每日计算依据'!J7*E${begin}`,J:`='每日计算依据'!I7*E${begin}`,L:`='每日计算依据'!N7*H${begin}`,M:`='每日计算依据'!O7*H${begin}`,
    O:`=IF(H${begin}=0,0,IF('每日计算依据'!R7>0,H${begin}*'每日计算依据'!W7,""))`,
    P:`=IF(H${begin}=0,0,IF('每日计算依据'!S7>0,H${begin}*'每日计算依据'!X7,""))`,
    Q:`=IF(H${begin}=0,0,IF('每日计算依据'!R7>0,H${begin}*'每日计算依据'!Y7,""))`,
    R:`=IF(H${begin}=0,0,IF('每日计算依据'!S7>0,H${begin}*'每日计算依据'!Z7,""))`})){calc.getRange(`${dest}${begin}`).formulas=[[f]];calc.getRange(`${dest}${begin}:${dest}${end}`).fillDown();}
}
const scalar={B:`=INDEX('参数与口径'!$B$22:$B$24,A7)`,E:`=INDEX('参数与口径'!$C$22:$C$24,A7)`,F:`='参数与口径'!$B$6*E7`,G:`='参数与口径'!$B$7*E7`,H:`='参数与口径'!$B$6*(1-E7)`,K:'=SUM(I7:J7)',N:'=SUM(L7:M7)',S:'=IF(COUNT(Q7:R7)>0,SUM(Q7:R7),"")',V:`=IF(ISNUMBER(P7),P7*'参数与口径'!$B$8^2,"")`,W:`=IF(ISNUMBER(O7),O7/'参数与口径'!$B$8^2,"")`,X:'=IF(ISNUMBER(V7),V7*U7,"")',Y:'=IF(ISNUMBER(W7),-W7*T7,"")',Z:'=IF(COUNT(Q7:R7)>0,SUM(Q7:R7,X7:Y7),"")',AA:'=SUM(K7,N7,S7)',AB:'=SUM(AA7,X7:Y7)'};
for(const [c,f]of Object.entries(scalar))seed(calc,c,f);
fmt(calc,`C7:C${last}`,'yyyy-mm-dd');fmt(calc,`D7:D${last}`,'yyyy-mm');fmt(calc,`E7:E${last}`,percent);fmt(calc,`F7:AB${last}`,money);fmt(calc,`AC7:AD${last}`,'0.00%');fmt(calc,`AE7:AG${last}`,integer);
calc.getRange(`AB7:AB${last}`).format.fill=light;calc.getRange(`AB7:AB${last}`).format.font.bold=true;
for(const c of ['B','C','D','E','F','G','H','I','J','L','M','O','P','Q','R','T','U','AC','AD','AE','AF','AG'])calc.getRange(`${c}7:${c}${last}`).format.font.color=green;
for(let i=0;i<33;i++)calc.getRangeByIndexes(0,i,3,1).format.columnWidth=i===0?10:[1,2,3].includes(i)?16:20;
calc.tables.add(`A6:AG${last}`,true,'DailyScenarioCalculation');calc.freezePanes.freezeRows(6);calc.freezePanes.freezeColumns(4);
for(const fn of deferred)fn();
wb.recalculate();
console.log('Workbook calculation complete');

const comparisons=[];
const keys=['da_net_eur','capacity_up_eur','capacity_down_eur','activation_up_cash_eur','activation_down_cash_eur','down_resale_value_eur','up_replenishment_cost_eur','activation_net_with_value_eur','total_cash_eur','total_with_value_eur'];
for(let s=0;s<3;s++){
 const vals=summary.getRange(`B${6+s}:K${6+s}`).values[0];
 vals.forEach((v,i)=>comparisons.push({kind:'total',scenario:s+1,key:keys[i],actual:v,expected:data.totals[s][keys[i]],difference:v-data.totals[s][keys[i]]}));
}
for(let m=0;m<data.monthly.length;m++){
 const item=data.monthly[m],vals=summary.getRange(`C${17+m}:L${17+m}`).values[0];
 vals.forEach((v,i)=>comparisons.push({kind:'month',scenario:item.scenario,month:item.month,key:keys[i],actual:v,expected:item[keys[i]],difference:v-item[keys[i]]}));
}
if(comparisons.some(x=>typeof x.actual!=='number'||Math.abs(x.difference)>1e-5))throw new Error('Excel vs Python reconciliation failed '+JSON.stringify(comparisons.filter(x=>Math.abs(x.difference)>1e-5)));
// Changing one allocation must update that case from the same input/build, with other cases intact.
const original=summary.getRange('K6:K8').values.map(x=>x[0]);
params.getRange('C23').values=[[1]];wb.recalculate();
const altered=summary.getRange('K7').values[0][0];
if(Math.abs(altered-original[0])>1e-5)throw new Error('Allocation recalculation failed');
params.getRange('C23').values=[[.5]];wb.recalculate();
if(Math.abs(summary.getRange('K7').values[0][0]-original[1])>1e-5)throw new Error('Allocation restoration failed');
console.log(JSON.stringify({totals:original,comparisons:comparisons.length,maxDifference:Math.max(...comparisons.map(x=>Math.abs(x.difference))),allocationTest:altered}));
const inspections=[];
for(const [name,r]of [['月度收益','A5:N8'],['月度收益','A33:N35'],['参数与口径','A21:F24'],['逐日计算','O525:AB526'],['每日计算依据','R7:AB8']])
  inspections.push((await wb.inspect({kind:'table',range:`'${name}'!${r}`,include:'values,formulas',tableMaxRows:5,tableMaxCols:14,maxChars:3500})).ndjson);
await fs.mkdir(outputDir,{recursive:true});
await fs.writeFile(work+'/verification.json',JSON.stringify({comparisons,allocationTest:{original,altered},inspections,chartSeries:chart.series.items.map(s=>({formula:s.formula,categoryFormula:s.categoryFormula}))},null,2));
for(const [sheetName,range,key]of [['月度收益','A1:N13','totals'],['月度收益','A16:N34','monthly_100'],['月度收益','A33:N51','monthly_50'],['月度收益','A50:N67','monthly_80'],['月度收益','A70:N89','chart'],['参数与口径','A5:F24','parameters'],['逐日计算','I524:AB529','daily_sample'],['每日计算依据','N7:AB12','coverage']]){
  const png=await wb.render({sheetName,range,scale:1.25,format:'png'});
  await fs.writeFile(work+`/${key}.png`,new Uint8Array(await png.arrayBuffer()));
}
console.log('Rendered all views');
const file=await SpreadsheetFile.exportXlsx(wb);
const filename=outputDir+'/西班牙_100MW200MWh_三策略月度收益_20250601_20261031.xlsx';
await file.save(filename);
console.log(JSON.stringify({output:filename,totals:original}));
