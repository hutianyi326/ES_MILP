/** Shared paths for the archived Artifact Tool workbook builders. */
import { parseArgs } from 'node:util';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';

const root=fileURLToPath(new URL('../../',import.meta.url));

export function excelPaths(defaults,description,extra={}){
  const options={help:{type:'boolean',short:'h'},...extra};
  for(const key of Object.keys(defaults))options[key]={type:'string'};
  const {values}=parseArgs({options,strict:true,allowPositionals:false});
  if(values.help){
    console.log(description+'\n\nRun from the repository root. Paths passed on the command line are relative to the current directory.');
    for(const [key,value]of Object.entries(defaults))console.log(`  --${key} <path>  (default: ${value})`);
    for(const key of Object.keys(extra))console.log(`  --${key}`);
    process.exit(0);
  }
  const result={};
  for(const [key,value]of Object.entries(defaults))result[key]=path.resolve(values[key]??path.join(root,value)).replaceAll('\\','/');
  for(const key of Object.keys(extra))result[key]=values[key]??false;
  if(result.qa)fs.mkdirSync(result.qa,{recursive:true});
  return result;
}
