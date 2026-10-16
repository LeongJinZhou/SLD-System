'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('web/app.js','utf8');
const names=['financialReportCanEdit','saveFinancialReport','flushFinancialReport','financeRecovery'];
const functions=names.map(name=>source.split(/\r?\n/).find(line=>line.startsWith(`function ${name}(`)||line.startsWith(`async function ${name}(`))).join('\n');
assert.ok(functions.includes('async function saveFinancialReport'));
const pending=[],requests=[];const context=vm.createContext({structuredClone,Error,JSON,document:{querySelector:()=>null},
 captureFinancialReport:()=>{},clearRecovery:()=>{},showFinancialRemoteChange:()=>{},
 api:(path,body)=>{requests.push({path,body});return new Promise((resolve,reject)=>pending.push({resolve,reject}));}});
vm.runInContext(`let financeInfo={can_prepare:true},financeDraft={proposal_id:'event',rows:[{kind:'income',description:'Old entry',amount:'10.00',budget_ref:'unplanned',evidence_ids:['receipt']}],variance_reason:'Reason',status:'draft'},
 financeEditVersion=1,financeSavedVersion=0,financeSavePromise=null,financeRemote=null,financeSaveError='',dirty=true;
 ${functions}
 globalThis.controls={save:saveFinancialReport,flush:flushFinancialReport,
 edit(){financeDraft.rows[0].description='Newer entry';financeEditVersion++;dirty=true;},
 state(){return {draft:financeDraft,dirty,remote:financeRemote};},
 backup(){return financeRecovery({...financeDraft,token:'secret',submitted_snapshot:'private',approved_at:'fake',can_prepare:true});}};`,context);
async function run(){
 const c=context.controls,save=c.save();assert.equal(requests.length,1);c.edit();
 pending.shift().resolve({report:{...requests[0].body.report,id:'report',revision:1,actual_income:'10.00',status:'draft'}});
 await new Promise(resolve=>setImmediate(resolve));assert.equal(requests.length,2);assert.equal(requests[1].body.report.rows[0].description,'Newer entry');assert.equal(requests[1].body.report.revision,1);
 pending.shift().resolve({report:{...requests[1].body.report,revision:2}});await save;assert.equal(c.state().dirty,false);assert.equal(c.state().draft.revision,2);
 c.edit();const failure=c.save();pending.shift().reject(Error('Offline'));await assert.rejects(failure,/Offline/);assert.equal(c.state().dirty,true);
 const backup=c.backup();assert.equal(backup.token,undefined);assert.equal(backup.submitted_snapshot,undefined);assert.equal(backup.can_prepare,undefined);assert.equal(backup.rows[0].description,'Newer entry');
 const conflict=c.save();const error=Error('Changed');error.status=409;pending.shift().reject(error);await new Promise(resolve=>setImmediate(resolve));pending.shift().resolve({can_prepare:true,report:{id:'report',revision:3,status:'pending_sld'}});await assert.rejects(conflict,/Changed/);assert.equal(c.state().remote.revision,3);assert.equal(c.state().draft.revision,2);assert.equal(c.state().dirty,true);
 await assert.rejects(c.save(),/newer actual report/);
 console.log('PASS: actual finance save serializes revisions, retains in-flight edits/failures, sanitizes recovery and blocks stale overwrite on conflict.');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
