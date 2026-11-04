import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const dir=path.resolve(process.argv[2]);
const python=process.argv[3] || 'python';
const {months,cases,labels}=JSON.parse(await fs.readFile(path.join(dir,'presentation.json'),'utf8'));
const wb=Workbook.create();
const [revenue,cap,act]=['月度收益与电量','容量价格','激活电价'].map(name=>wb.worksheets.add(name));
const money='#,##0.00;(#,##0.00);0.00';
function put(sh,row,col,rows){sh.getRangeByIndexes(row-1,col-1,rows.length,rows[0].length).values=rows;}
function head(sh,row,col,values){
 put(sh,row,col,[values]);
 sh.getRangeByIndexes(row-1,col-1,1,values.length).format={fill:'#20415C',font:{color:'#FFFFFF',bold:true,size:10},rowHeight:30,wrapText:true,verticalAlignment:'center'};
}
function title(sh,row,col,value){
 put(sh,row,col,[[value]]);
 sh.getCell(row-1,col-1).format.font={name:'Arial',bold:true,size:14,color:'#20415C'};
}
function formula(sh,r,c,expr){sh.getCell(r-1,c-1).formulas=[[expr]];}
const serial=m=>Date.parse(m+'-01T00:00:00Z')/86400000+25569;
for(const sh of [revenue,cap,act])sh.showGridLines=false;
title(revenue,2,1,'西班牙储能月度收益与交流侧电量');
put(revenue,3,1,[['2025年6月—2026年10月　金额 EUR，电量 MWh。售电价值与补能收支计入激活发生月。']]);
put(revenue,4,1,[['堆积图场景',cases[3]]]);
revenue.getRange('B4').dataValidation={rule:{type:'list',values:cases}};
revenue.getRange('B4').format.fill='#FFF0BE';
put(revenue,5,1,[['滚动年收益取含当月的连续12个完整交付月，除以项目充放电功率较大值（四个场景均为100 MW）。前11个月留空。']]);
head(revenue,7,1,['策略','月份',...labels]);
for(let k=0;k<4;k++){
 const row=8+k*17;
 put(revenue,row,1,months.map(m=>[cases[k],serial(m.month),...m.cases[k]]));
}
revenue.getRange('B8:B75').setNumberFormat('yyyy-mm');
revenue.getRange('C8:O75').setNumberFormat(money);
revenue.getRange('O8:O75').format.fill='#E4F0E8';
revenue.getRange('A1').format.columnWidth=28;revenue.getRange('B1').format.columnWidth=29;
revenue.getRange('C1:O1').format.columnWidth=17;
revenue.freezePanes.freezeRows(7);revenue.freezePanes.freezeColumns(2);
head(revenue,79,1,['滚动截至月',...cases]);
head(revenue,99,1,['月份',...labels.slice(4,11),'含估值净总额']);
const cols='GHIJKLMO';
for(let i=0;i<17;i++){
 put(revenue,80+i,1,[[months[i].month]]);
 put(revenue,100+i,1,[[months[i].month]]);
 for(let k=0;k<4;k++)if(i>=11){
  const end=8+17*k+i;formula(revenue,80+i,k+2,'=SUM(O'+(end-11)+':O'+end+')/100');
 }
 for(let j=0;j<8;j++){
  const c=cols[j], dateRow=8+i;
  formula(revenue,100+i,j+2,'=SUMIFS($'+c+'$8:$'+c+'$75,$A$8:$A$75,$B$4,$B$8:$B$75,$B'+dateRow+')');
 }
}
revenue.getRange('B80:E96').setNumberFormat(money);
revenue.getRange('B100:I116').setNumberFormat(money);
title(cap,2,1,'aFRR容量价格　EUR/MW/15分钟');
put(cap,3,1,[['当地小时均价按15分钟样本等权，P25、P50和P75取当月全部15分钟原价。']]);
title(act,2,1,'aFRR激活电价与配对DA电价　EUR/MWh');
put(act,3,1,[['按马德里当地小时聚合。每个方向仅取该方向激活价有效的4秒点，配对所属15分钟DA。空白表示没有有效样本。']]);
for(const sh of [cap,act])sh.getRange('A1:Z1').format.columnWidth=15;
for(let i=0;i<17;i++){
 const m=months[i],r=6+34*i;
 title(cap,r,1,m.month+'　容量价格');
 head(cap,r+1,1,['当地小时','Up均价','Dn均价']);
 put(cap,r+2,1,m.capacity.map((v,h)=>[h,...v]));
 cap.getRange('B'+(r+2)+':C'+(r+25)).setNumberFormat(money);
 head(cap,r+27,5,['全月原价','P25','P50（中位数）','P75']);
 put(cap,r+28,5,m.cap_quantiles.map((v,k)=>[k?'Dn':'Up',...v]));
 cap.getRange('F'+(r+28)+':H'+(r+29)).setNumberFormat(money);
 put(cap,r+30,5,[[m.cap_quantiles.map((v,k)=>(k?'Dn':'Up')+'中位数 '+v[1].toFixed(2)+'，中间50%落在 '+v[0].toFixed(2)+' 至 '+v[2].toFixed(2)).join('。')+'。']]);
 title(act,r,1,m.month+'　激活与DA');
 for(const [k,direction] of ['up','down'].entries()){
  const offset=k*12, z=m.activation[direction], name=k?'Dn':'Up';
  head(act,r+1,1+offset,['当地小时',name+'激活均价','配对DA均价']);
  put(act,r+2,1+offset,z.hourly.map((v,h)=>[h,...v]));
  act.getRangeByIndexes(r+1,1+offset,24,2).setNumberFormat(money);
  head(act,r+27,5+offset,[k?'DA − Dn':'Up − DA','平均价差','P75','P25','有效4秒数']);
  put(act,r+28,5+offset,[['全月',...z.spread,z.valid]]);
  act.getRangeByIndexes(r+27,5+offset,1,3).setNumberFormat(money);
 }
}
wb.recalculate();
for(let k=0;k<4;k++){
 put(revenue,4,2,[[cases[k]]]);wb.recalculate();
 for(let i=0;i<17;i++){
  const got=revenue.getCell(99+i,8).values[0][0];
  if(typeof got!=='number'||Math.abs(got-months[i].cases[k][12])>1e-5)throw Error('Selector mismatch '+i);
 }
}
const base=path.join(dir,'.presentation-grid.xlsx');
await (await SpreadsheetFile.exportXlsx(wb)).save(base);
const result=spawnSync(python,[fileURLToPath(new URL('./simple_presentation_charts.py',import.meta.url)),dir],{stdio:'inherit'});
if(result.status!==0)throw Error('Chart export failed');
await fs.unlink(base);
