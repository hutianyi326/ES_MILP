"""Attach native Excel combination charts to Artifact Tool worksheets."""
import json
from io import BytesIO
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

import xlsxwriter

COLORS = ["#26766B","#C37433","#456C98","#995775","#A44E54","#849946","#705081"]
SHEETS = ["月度收益与电量","容量价格","激活电价"]


def build(dir):
    data=json.loads((dir/"presentation.json").read_text(encoding="utf-8"))
    months=data["months"]
    chart_stream=BytesIO()
    book=xlsxwriter.Workbook(chart_stream,{"in_memory":True})
    sheets=[book.add_worksheet(s) for s in SHEETS]
    sizes={name:[] for name in SHEETS}

    def series(chart,sheet,name,cats,vals,catdata,valdata,**options):
        chart.add_series(dict(name=name,categories=f"='{sheet}'!{cats}",values=f"='{sheet}'!{vals}",
                              categories_data=catdata,values_data=valdata,**options))

    def place(chart,sheet,row,col,title,unit,width=720,height=400):
        chart.set_title({"name":title,"name_font":{"size":12}})
        axis_font={"color":"#38475A","size":9}
        chart.set_x_axis({"num_font":axis_font,"label_position":"low"})
        chart.set_y_axis({"name":unit,"num_format":"#,##0.##","num_font":axis_font,
                          "major_gridlines":{"visible":True,"line":{"color":"#E1E6EA","width":0.5}}})
        chart.set_legend({"position":"bottom","font":{"size":9}})
        chart.set_size({"width":width,"height":height})
        sizes[sheet.name].append((width,height))
        sheet.insert_chart(row,col,chart)

    labels=[m["month"] for m in months]
    roll=book.add_chart({"type":"line"})
    for k,name in enumerate(data["cases"]):
        col="BCDE"[k]
        values=[None if i<11 else sum(m["cases"][k][-1] for m in months[i-11:i+1])/100 for i in range(17)]
        series(roll,SHEETS[0],name,"$A$80:$A$96",f"${col}$80:${col}$96",labels,values,
               line={"color":COLORS[k],"width":2})
    place(roll,sheets[0],6,16,"过去12个完整月的含估值收益","EUR/MW")
    stacked=book.add_chart({"type":"column","subtype":"stacked"})
    for j,name in enumerate(data["labels"][4:11]):
        col="BCDEFGH"[j]
        series(stacked,SHEETS[0],name,"$A$100:$A$116",f"${col}$100:${col}$116",labels,[m["cases"][3][4+j] for m in months],
               fill={"color":COLORS[j]},border={"none":True})
    net=book.add_chart({"type":"line"})
    series(net,SHEETS[0],"含估值净总额","$A$100:$A$116","$I$100:$I$116",labels,[m["cases"][3][-1] for m in months],
           line={"none":True},marker={"type":"diamond","size":4,"border":{"color":"#263444"}},
           data_labels={"value":True,"position":"above","num_format":"#,##0.00","font":{"size":8}})
    stacked.combine(net)
    place(stacked,sheets[0],29,16,"所选场景月度收益构成及净总额","EUR",1020,470)
    for i,m in enumerate(months):
        row=6+34*i
        start,end=row+2,row+25
        cats=list(range(24))
        cap=book.add_chart({"type":"line"})
        for k,col in enumerate("BC"):
            series(cap,SHEETS[1],["Up","Dn"][k],f"$A${start}:$A${end}",f"${col}${start}:${col}${end}",cats,[v[k] for v in m["capacity"]],line={"color":COLORS[k]})
        place(cap,sheets[1],row,4,m["month"]+" 容量价格","EUR/MW/15分钟",600,335)
        for k,direction in enumerate(["up","down"]):
            z=m["activation"][direction]["hourly"]
            colcat,colact,colda=("A","B","C") if not k else ("M","N","O")
            ref=lambda col:f"${col}${start}:${col}${end}"
            bars=book.add_chart({"type":"column"})
            series(bars,SHEETS[2],direction.upper()+" 激活",ref(colcat),ref(colact),cats,[v[0] for v in z],fill={"color":COLORS[k]})
            line=book.add_chart({"type":"line"})
            series(line,SHEETS[2],"配对DA（右轴）",ref(colcat),ref(colda),cats,[v[1] for v in z],y2_axis=True,line={"color":"#193B65","width":2})
            line.set_y2_axis({"name":"DA EUR/MWh","num_format":"0.00","num_font":{"color":"#38475A","size":9},"major_gridlines":{"visible":False}})
            bars.combine(line)
            place(bars,sheets[2],row,4+k*12,m["month"]+" "+direction.upper()+" 激活与配对DA","激活 EUR/MWh",640,335)
    book.close()
    target=dir/"西班牙储能_月度收益与价格统计.xlsx"
    tmp=target.with_suffix(".tmp")
    # Keep all sheet cells, formula caches, styles and validation from the grid workbook.
    with ZipFile(dir/".presentation-grid.xlsx") as grid, ZipFile(chart_stream) as charts, ZipFile(tmp,"w",ZIP_DEFLATED) as dst:
        for name in grid.namelist():
            body=grid.read(name)
            if name=="[Content_Types].xml":
                tree=ET.fromstring(body)
                for node in ET.fromstring(charts.read(name)):
                    if node.get("PartName","").startswith(("/xl/charts/","/xl/drawings/")):tree.append(node)
                body=ET.tostring(tree,encoding="utf-8",xml_declaration=True)
            for idx in range(1,4):
                if name==f"xl/worksheets/sheet{idx}.xml":
                    endtag=b"</x:worksheet>" if b"</x:worksheet>" in body else b"</worksheet>"
                    prefix="x:" if b"x:" in endtag else ""
                    tag=f'<{prefix}drawing xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:id="rId1"/>'.encode()
                    assert endtag in body
                    body=body.replace(endtag,tag+endtag)
            dst.writestr(name,body)
        for name in charts.namelist():
            if name.startswith(("xl/drawings/","xl/charts/","xl/worksheets/_rels/")):
                assert name not in grid.namelist(),name
                body=charts.read(name)
                if name in [f"xl/drawings/drawing{i}.xml" for i in range(1,4)]:
                    # Donor cells use different widths. Use a fixed extent so plots cannot cover adjacent tables.
                    idx=int(name.rsplit("drawing",1)[1].split(".")[0])-1
                    ns="{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}"
                    tree=ET.fromstring(body)
                    for anchor,(width,height) in zip(tree,sizes[SHEETS[idx]],strict=True):
                        anchor.tag=ns+"oneCellAnchor"
                        anchor.attrib.clear()
                        anchor.remove(anchor.find(ns+"to"))
                        anchor.insert(1,ET.Element(ns+"ext",{"cx":str(width*9525),"cy":str(height*9525)}))
                    body=ET.tostring(tree,encoding="utf-8",xml_declaration=True)
                dst.writestr(name,body)
    from openpyxl import load_workbook
    wb=load_workbook(tmp.open("rb"),data_only=True)
    assert wb.sheetnames==SHEETS and [len(sh._charts) for sh in wb]==[2,17,34]
    for ch in wb.worksheets[2]._charts:
        assert len(ch._charts)==2 and ch._charts[0].y_axis.axId!=ch._charts[1].y_axis.axId
    assert len(wb.worksheets[0].data_validations.dataValidation)==1
    for k in range(4):
        for i,m in enumerate(months):
            for j,v in enumerate(m["cases"][k]):
                assert abs(wb.worksheets[0].cell(8+17*k+i,3+j).value-v)<1e-5
            val=wb.worksheets[0].cell(80+i,2+k).value
            if i<11:assert val is None
            else:assert abs(val-sum(x["cases"][k][-1] for x in months[i-11:i+1])/100)<1e-6
    wb.close()
    tmp.replace(target)
    print(target,flush=True)


if __name__=="__main__":
    build(Path(sys.argv[1]))
