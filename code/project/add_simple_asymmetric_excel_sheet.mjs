import fs from 'node:fs/promises';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
import { excelPaths } from './simple_excel_cli.mjs';

const paths=excelPaths({input:'output/excel_monthly/outputs/simple_model/西班牙_100MW200MWh_三策略月度收益_新增80%现货明细_20261104.xlsx',output:'output/excel_monthly/outputs/simple_model/西班牙_月度收益_新增充50放100MW_80%现货_20261104.xlsx',source:'output/simple_asymmetric_50_100_200_80pct_20261104',qa:'output/simple_excel_qa/asymmetric'},'Append the 50/100 MW, 200 MWh, 80% DA monthly and daily calculations.',{'inspect-only':{type:'boolean'}});
const old=paths.input,dest=paths.output,work=paths.qa,dataDir=paths.source;
const data=JSON.parse(await fs.readFile(dataDir+'/results.json','utf8'));
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(old));
console.log('Latest workbook imported');
if(process.argv.includes('--inspect-only')){
 console.log((await wb.inspect({kind:'table',range:"'80%现货月度收益'!A21:O24",include:'values,formulas',tableMaxRows:4,tableMaxCols:15,maxChars:3500})).ndjson);
 const before=await wb.render({sheetName:'80%现货月度收益',range:'A1:O14',scale:1,format:'png'});
 await fs.writeFile(work+'/before_asymmetric.png',new Uint8Array(await before.arrayBuffer()));
 process.exit(0);
}
const sh=wb.worksheets.add('充50放100_80%现货');
const first=40,last=first+data.daily.length-1;
const navy='#203A5F',ink='#182433',green='#15803D',light='#EDF2F7';
const money='#,##0.00;(#,##0.00);"—"',num='#,##0.0000;(#,##0.0000);"—"';
const serial=s=>Date.parse(s+'T00:00:00Z')/86400000+25569;
sh.showGridLines=false;sh.tabColor=navy;
sh.getRange(`A1:Z${last}`).format={font:{name:'Arial',size:10,color:ink},verticalAlignment:'center',rowHeight:23};
sh.getRange('A2').values=[['充电50 MW、放电100 MW、200 MWh：80%现货收益']];
sh.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:navy};
sh.getRange('A3').values=[['2025-06-01至2026-10-31，共518天。金额EUR，支出记负数。DA按本次充放电功率重新搜索每日窗口。']];
sh.getRange('A3').format.font.italic=true;
sh.getRange('A4:J4').values=[['充电上限 MW',50,'放电上限 MW',100,'直流电量 MWh',200,'DA比例',.8,'单向效率',.92]];
sh.getRange('A5:J5').values=[['DA充电 MW',null,'DA放电 MW',null,'DA电量 MWh',null,'aFRR Up MW',null,'aFRR Dn MW',null]];
for(const [c,f]of [['B5','=B4*H4'],['D5','=D4*H4'],['F5','=F4*H4'],['H5','=D4*(1-H4)'],['J5','=B4*(1-H4)']])sh.getRange(c).formulas=[[f]];
for(const c of ['B4','D4','F4','B5','D5','F5','H5','J5'])sh.getRange(c).setNumberFormat('0.00');
sh.getRange('H4').setNumberFormat('0.0%');sh.getRange('J4').setNumberFormat('0.0%');
for(const c of ['B4','D4','F4','H4','J4'])sh.getRange(c).format.fill=light;
function header(address){sh.getRange(address).format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,rowHeight:46};}
function seed(c,f){sh.getRange(`${c}${first}`).formulas=[[f]];sh.getRange(`${c}${first}:${c}${last}`).fillDown();}

// One requested sheet contains monthly results above a transparent daily build.
const dailyHead=['交付日','月份','DA充电 MWh','DA放电 MWh','DA购电收支 EUR','DA售电收入 EUR','DA净收益 EUR','Up容量 EUR','Dn容量 EUR','Up激活 MWh','Dn激活 MWh','Up激活收入 EUR','Dn激活收支 EUR','当日DA P25','当日DA P75','Dn后续售电价值','Up潜在补能收支','aFRR电量净额','当期收支合计','含估值总收益','全日4秒数','Up有价4秒数','Dn有价4秒数','DA循环深度','DA充电开始 含偏移','DA放电开始 含偏移'];
sh.getRange('A39:Z39').values=[dailyHead];header('A39:Z39');
const rows=data.daily.map(d=>[serial(d.date),serial(d.month+'-01'),d.da_buy_mwh,d.da_sell_mwh,d.da_purchases_eur,d.da_sales_eur,...Array(17).fill(null),d.da_depth,d.charge_start?'当地 '+d.charge_start:'',d.discharge_start?'当地 '+d.discharge_start:'']);
if(rows.some(r=>r.length!==26))throw new Error('Daily row length');
sh.getRange(`A${first}:Z${last}`).values=rows;
const daily={G:`=SUM(E${first}:F${first})`,H:`='每日计算依据'!N7*$H$5`,I:`='每日计算依据'!O7*$J$5`,
 J:`=IF('每日计算依据'!R7>0,'每日计算依据'!W7*$H$5,"")`,
 K:`=IF('每日计算依据'!S7>0,'每日计算依据'!X7*$J$5,"")`,
 L:`=IF('每日计算依据'!R7>0,'每日计算依据'!Y7*$H$5,"")`,
 M:`=IF('每日计算依据'!S7>0,'每日计算依据'!Z7*$J$5,"")`,
 N:"='每日计算依据'!E7",O:"='每日计算依据'!F7",
 P:`=IF(ISNUMBER(K${first}),K${first}*$J$4^2*O${first},"")`,
 Q:`=IF(ISNUMBER(J${first}),-J${first}/$J$4^2*N${first},"")`,
 R:`=IF(COUNT(L${first}:M${first})>0,SUM(L${first}:M${first},P${first}:Q${first}),"")`,
 S:`=SUM(G${first}:I${first},L${first}:M${first})`,T:`=SUM(S${first},P${first}:Q${first})`,
 U:"='每日计算依据'!T7",V:"='每日计算依据'!R7",W:"='每日计算依据'!S7"};
for(const [c,f]of Object.entries(daily))seed(c,f);
sh.getRange(`A${first}:A${last}`).setNumberFormat('yyyy-mm-dd');sh.getRange(`B${first}:B${last}`).setNumberFormat('yyyy-mm');
sh.getRange(`C${first}:T${last}`).setNumberFormat(money);sh.getRange(`U${first}:W${last}`).setNumberFormat('#,##0');sh.getRange(`X${first}:X${last}`).setNumberFormat('0.0%');
for(const c of ['H','I','J','K','L','M','N','O','U','V','W'])sh.getRange(`${c}${first}:${c}${last}`).format.font.color=green;
sh.getRange(`T${first}:T${last}`).format.fill=light;sh.getRange(`T${first}:T${last}`).format.font.bold=true;

const headings=['月份','DA净收益','Up容量收益','Dn容量收益','容量收益合计','Up激活收入','Dn激活收支','激活收支合计','Dn后续售电价值','Up潜在补能收支','aFRR电量净额','当期收支合计','含估值总收益','Up有价率','Dn有价率'];
sh.getRange('A8:O8').values=[headings];header('A8:O8');
const sumMonth=(c,r)=>`SUMIFS($${c}$${first}:$${c}$${last},$B$${first}:$B$${last},$A${r})`;
for(let i=0;i<17;i++){
 const r=9+i;sh.getRange(`A${r}`).values=[[serial(data.monthly[i].month+'-01')]];
 for(const [c,src]of Object.entries({B:'G',C:'H',D:'I',F:'L',G:'M',I:'P',J:'Q',K:'R',L:'S',M:'T'}))sh.getRange(`${c}${r}`).formulas=[['='+sumMonth(src,r)]];
 sh.getRange(`E${r}`).formulas=[[`=SUM(C${r}:D${r})`]];sh.getRange(`H${r}`).formulas=[[`=SUM(F${r}:G${r})`]];
 sh.getRange(`N${r}`).formulas=[['='+sumMonth('V',r)+'/'+sumMonth('U',r)]];
 sh.getRange(`O${r}`).formulas=[['='+sumMonth('W',r)+'/'+sumMonth('U',r)]];
 if(i%2===1)sh.getRange(`A${r}:O${r}`).format.fill='#F1F5F9';
}
sh.getRange('A9:A25').setNumberFormat('yyyy-mm');sh.getRange('B9:M26').setNumberFormat(money);sh.getRange('N9:O26').setNumberFormat('0.00%');
sh.getRange('A26').values=[['合计（518天）']];for(const c of 'BCDEFGHIJKLM')sh.getRange(`${c}26`).formulas=[[`=SUM(${c}9:${c}25)`]];
sh.getRange('N26:O26').formulas=[[`=SUM(V${first}:V${last})/SUM(U${first}:U${last})`,`=SUM(W${first}:W${last})/SUM(U${first}:U${last})`]];
sh.getRange('A26:O26').format.fill='#E3EBF4';sh.getRange('A26:O26').format.font.bold=true;
sh.getRange('A26:O26').format.borders={top:{style:'medium',color:'#7C91A8'}};
sh.getRange('M9:M26').format.fill=light;sh.getRange('M9:M26').format.font.bold=true;
sh.getRange('A28').values=[['当期收支合计＝DA净收益＋Up/Dn容量＋Up/Dn激活收支；含估值总收益再加Dn后续售电价值与Up潜在补能收支。']];
sh.getRange('A29').values=[['Dn售电按当日DA P75、Up补能按P25，均计两次92%效率；两项为潜在估值，计入激活发生月。']];
sh.getRange('A30').values=[['容量报价Up/Dn均1 EUR/MW/15分钟；激活价差阈值Up 200、Dn 0 EUR/MWh；出清价及价差均严格大于报价/阈值才触发。']];
sh.getRange('A31').values=[['aFRR沿用无SOC限制、双向独立筛选；缺失激活价不补零，仅汇总可计算部分。有价率是市场数据覆盖率。']];
sh.getRange('A32').values=[['DA按40 MW充电、80 MW放电、160 MWh，每日一次先充后放并按1%深度搜索；属于事后已知价格的窗口测算。']];
sh.getRange('A33').values=[['本次固定配置；更改功率、电量、效率或DA比例，需重新运行DA窗口搜索。aFRR每MW价格积分复用此前逐4秒筛选依据。']];
sh.getRange('A34').values=[['价格来自此前整理的OMIE、REE/eSIOS与ENTSO-E官方数据，来源和缺失处理见“参数与口径”。未扣税费、退化及运营成本。']];
for(let r=28;r<=34;r++)sh.getRange(`A${r}`).format.font.color='#526277';
sh.getRange('A37').values=[['逐日计算与汇总依据']];sh.getRange('A37').format.font.bold=true;
sh.getRange('A38').values=[['DA充放电量及购售电收支为新配置窗口搜索结果；aFRR价格积分、日度分位价和覆盖点数引用“每日计算依据”。']];
for(const c of 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')sh.getRange(`${c}1:${c}3`).format.columnWidth=c==='A'?19:['N','O'].includes(c)?14:['Y','Z'].includes(c)?42:21;
sh.freezePanes.freezeRows(8);sh.freezePanes.freezeColumns(1);
wb.recalculate();

const keys=['da_net_eur','capacity_up_eur','capacity_down_eur','capacity_total_eur','activation_up_cash_eur','activation_down_cash_eur','activation_cash_eur','down_resale_value_eur','up_replenishment_cost_eur','activation_net_with_value_eur','total_cash_eur','total_with_value_eur','up_price_coverage','down_price_coverage'];
let maxDifference=0,comparisons=0;
for(let i=0;i<17;i++){
 const vals=sh.getRange(`B${9+i}:O${9+i}`).values[0];
 vals.forEach((v,j)=>{const error=Math.abs(v-data.monthly[i][keys[j]]);if(typeof v!=='number'||error>1e-5)throw new Error('Monthly mismatch '+i+' '+keys[j]);comparisons++;maxDifference=Math.max(maxDifference,error);});
}
for(const [c,key]of Object.entries({B:'da_net_eur',C:'capacity_up_eur',D:'capacity_down_eur',E:'capacity_total_eur',F:'activation_up_cash_eur',G:'activation_down_cash_eur',H:'activation_cash_eur',I:'down_resale_value_eur',J:'up_replenishment_cost_eur',K:'activation_net_with_value_eur',L:'total_cash_eur',M:'total_with_value_eur'})){
 const v=sh.getRange(`${c}26`).values[0][0],error=Math.abs(v-data.totals[key]);if(error>1e-5)throw new Error('Total mismatch '+key);comparisons++;maxDifference=Math.max(maxDifference,error);
}
// Reconcile daily calculations too, including null prices excluded rather than zero-filled.
for(let i=0;i<data.daily.length;i++){
 const vals=sh.getRange(`G${first+i}:T${first+i}`).values[0],d=data.daily[i];
 const mapped={0:'da_net_eur',1:'capacity_up_eur',2:'capacity_down_eur',3:'up_energy_mwh',4:'down_energy_mwh',5:'activation_up_cash_eur',6:'activation_down_cash_eur',7:'da_p25',8:'da_p75',9:'down_resale_value_eur',10:'up_replenishment_cost_eur',11:'activation_net_with_value_eur',12:'total_cash_eur',13:'total_with_value_eur'};
 for(const [j,key]of Object.entries(mapped)){
  const v=vals[j];if(v===''){if(Math.abs(d[key])>1e-8)throw new Error('Unexpected blank '+i+' '+key);continue;}
  const error=Math.abs(v-d[key]);if(typeof v!=='number'||error>1e-5)throw new Error('Daily mismatch '+i+' '+key);comparisons++;maxDifference=Math.max(maxDifference,error);
 }
}
console.log((await wb.inspect({kind:'table',range:"'充50放100_80%现货'!A23:O26",include:'values,formulas',tableMaxRows:4,tableMaxCols:15,maxChars:3500})).ndjson);
await fs.writeFile(work+'/asymmetric_excel_verification.json',JSON.stringify({comparisons,maxDifference,total:sh.getRange('M26').values[0][0],source:old,destination:dest},null,2));
for(const [range,key]of [['A1:O16','top'],['A17:O34','bottom'],['G39:T44','daily']]){
 const png=await wb.render({sheetName:sh.name,range,scale:1.1,format:'png'});
 await fs.writeFile(work+`/asymmetric_${key}.png`,new Uint8Array(await png.arrayBuffer()));
}
await(await SpreadsheetFile.exportXlsx(wb)).save(dest);
console.log(JSON.stringify({destination:dest,comparisons,maxDifference,total:sh.getRange('M26').values[0][0]}));
