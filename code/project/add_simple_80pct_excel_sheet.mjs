import fs from 'node:fs/promises';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
import { excelPaths } from './simple_excel_cli.mjs';

const paths=excelPaths({input:'output/excel_monthly/outputs/simple_model/西班牙_100MW200MWh_三策略月度收益_20250601_20261031.xlsx',output:'output/excel_monthly/outputs/simple_model/西班牙_100MW200MWh_三策略月度收益_新增80%现货明细_20261104.xlsx',source:'output/simple_period_20250601_20261031_20261103',qa:'output/simple_excel_qa/80pct'},'Append the monthly 80% DA view.',{'inspect-only':{type:'boolean'}});
const old=paths.input,dest=paths.output,work=paths.qa;
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(old));
console.log('Workbook imported');
if(process.argv.includes('--inspect-only')){
 console.log((await wb.inspect({kind:'table',range:"'月度收益'!A50:N53",include:'values,formulas',tableMaxRows:4,tableMaxCols:14,maxChars:4000})).ndjson);
 const before=await wb.render({sheetName:'月度收益',range:'A16:N20',scale:1.1,format:'png'});
 await fs.writeFile(work+'/before_add80.png',new Uint8Array(await before.arrayBuffer()));
 process.exit(0);
}
const existingNames=['月度收益','参数与口径','逐日计算','每日计算依据'];
const oldValues=wb.worksheets.getItem('月度收益').getRange('A5:N8').values;
const sh=wb.worksheets.add('80%现货月度收益');
const navy='#203A5F',ink='#182433',money='#,##0.00;(#,##0.00);"—"';
sh.showGridLines=false;sh.tabColor=navy;
sh.getRange('A1:O29').format={font:{name:'Arial',size:10,color:ink},verticalAlignment:'center',rowHeight:23};
sh.getRange('A2').values=[['80%现货策略月度收益']];
sh.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:navy};
sh.getRange('A3').values=[['2025-06-01至2026-10-31；100 MW / 200 MWh。金额为EUR，支出取负数；对应“参数与口径”第3策略。']];
sh.getRange('A3').format.font.italic=true;
sh.getRange('A4:H4').values=[['DA比例',null,'DA功率 MW',null,'DA电量 MWh',null,'aFRR各方向 MW',null]];
for(const [cell,ref]of [['B4','C24'],['D4','D24'],['F4','E24'],['H4','F24']])sh.getRange(cell).formulas=[[`='参数与口径'!${ref}`]];
sh.getRange('B4').setNumberFormat('0.0%');for(const c of ['D4','F4','H4'])sh.getRange(c).setNumberFormat('0.00');
const headings=['月份','DA净收益','Up容量收益','Dn容量收益','容量收益合计','Up激活收入','Dn激活收支','激活收支合计','Dn后续售电价值','Up潜在补能收支','aFRR电量净额','当期收支合计','含估值总收益','Up有价率','Dn有价率'];
sh.getRange('A6:O6').values=[headings];
sh.getRange('A6:O6').format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,rowHeight:46};
const links={A:'B',B:'C',C:'D',D:'E',F:'F',G:'G',I:'H',J:'I',K:'J',L:'K',M:'L',N:'M',O:'N'};
for(let i=0;i<17;i++){
 const r=7+i,sourceRow=51+i;
 for(const [c,src]of Object.entries(links))sh.getRange(`${c}${r}`).formulas=[[`='月度收益'!${src}${sourceRow}`]];
 sh.getRange(`E${r}`).formulas=[[`=SUM(C${r}:D${r})`]];
 sh.getRange(`H${r}`).formulas=[[`=SUM(F${r}:G${r})`]];
 if(i%2===1)sh.getRange(`A${r}:O${r}`).format.fill='#F1F5F9';
}
sh.getRange('A7:A23').setNumberFormat('yyyy-mm');sh.getRange('B7:M24').setNumberFormat(money);sh.getRange('N7:O24').setNumberFormat('0.00%');
sh.getRange('A24').values=[['合计（518天）']];
for(const c of 'BCDEFGHIJKLM')sh.getRange(`${c}24`).formulas=[[`=SUM(${c}7:${c}23)`]];
sh.getRange('N24:O24').formulas=[["='月度收益'!L8","='月度收益'!M8"]];
sh.getRange('A24:O24').format.fill='#E3EBF4';sh.getRange('A24:O24').format.font.bold=true;
sh.getRange('A24:O24').format.borders={top:{style:'medium',color:'#7C91A8'}};
sh.getRange('M7:M24').format.fill='#EDF2F7';sh.getRange('M7:M24').format.font.bold=true;
sh.getRange('A26').values=[['当期收支合计＝DA净收益＋容量收益合计＋激活收支合计；含估值总收益再加Dn后续售电价值与Up潜在补能收支。']];
sh.getRange('A27').values=[['Dn后续售电按当日DA P75、Up补能按P25，均计两次92%效率；这两项为潜在估值，计入激活发生月。']];
sh.getRange('A28').values=[['沿用原模型：aFRR不限制SOC、上下调独立筛选；空激活价不补零，金额汇总可计算部分，有价率按实际时长加权。']];
for(const r of [26,27,28])sh.getRange(`A${r}`).format.font.color='#526277';
for(const c of 'ABCDEFGHIJKLMNO')sh.getRange(`${c}1:${c}3`).format.columnWidth=c==='A'?19:['N','O'].includes(c)?14:21;
sh.freezePanes.freezeRows(6);sh.freezePanes.freezeColumns(1);
wb.recalculate();
const expected=JSON.parse(await fs.readFile(paths.source+'/results.json','utf8')).monthly.filter(x=>x.scenario==='80% DA');
const keys=['da_net_eur','capacity_up_eur','capacity_down_eur','capacity_total_eur','activation_up_cash_eur','activation_down_cash_eur','activation_cash_eur','down_resale_value_eur','up_replenishment_cost_eur','activation_net_with_value_eur','total_cash_eur','total_with_value_eur','up_price_coverage','down_price_coverage'];
let maxDifference=0,comparisons=0;
for(let i=0;i<17;i++){
 const vals=sh.getRange(`B${7+i}:O${7+i}`).values[0];
 for(let j=0;j<keys.length;j++){
  const error=Math.abs(vals[j]-expected[i][keys[j]]);
  if(typeof vals[j]!=='number'||error>1e-5)throw new Error('Monthly comparison failed '+i+' '+keys[j]);
  maxDifference=Math.max(maxDifference,error);comparisons++;
 }
}
if(Math.abs(sh.getRange('M24').values[0][0]-23096173.779338744)>1e-5)throw new Error('Total mismatch');
if(JSON.stringify(oldValues)!==JSON.stringify(wb.worksheets.getItem('月度收益').getRange('A5:N8').values))throw new Error('Existing summary changed');
for(let i=0;i<4;i++)if(wb.worksheets.getItemAt(i).name!==existingNames[i])throw new Error('Existing sheet order changed');
console.log((await wb.inspect({kind:'table',range:"'80%现货月度收益'!A21:O24",include:'values,formulas',tableMaxRows:4,tableMaxCols:15,maxChars:4000})).ndjson);
await fs.writeFile(work+'/add80_verification.json',JSON.stringify({comparisons,maxDifference,total:sh.getRange('M24').values[0][0],source:old,destination:dest},null,2));
for(const [range,key]of [['A1:O14','top'],['A15:O28','bottom']]){
 const png=await wb.render({sheetName:sh.name,range,scale:1.1,format:'png'});
 await fs.writeFile(work+`/added80_${key}.png`,new Uint8Array(await png.arrayBuffer()));
}
await(await SpreadsheetFile.exportXlsx(wb)).save(dest);
console.log(JSON.stringify({destination:dest,comparisons,maxDifference,total:sh.getRange('M24').values[0][0]}));
