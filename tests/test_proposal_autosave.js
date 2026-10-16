'use strict';
// Run the real controller with mocked transport; this is not browser interaction QA.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('web/app.js','utf8');
const loader=require('./helpers/source_loader').createSourceLoader(source);
const controller=loader.section('PROPOSAL_AUTOSAVE');
function setup(api){
 const context=vm.createContext({structuredClone,Error,api,crypto:{randomUUID:()=> '12345678-1234-4234-8234-123456789012'},clearTimeout:()=>{},setTimeout:()=>1,
  document:{querySelector:()=>null},captureProposal:()=>{},proposalCanEdit:p=>['draft','returned'].includes(p.status||'draft'),
  updateProposalProgress:()=>{},showRequestError:()=>{},sessionError:()=>Error('Session expired'),clearRecovery:()=>{}});
 vm.runInContext(`let state={proposals:[]},proposalDraft={club_id:'club',title:'',summary:'First draft',status:'draft'},dirty=false,sessionExpired=false;
 ${controller}
 globalThis.controls={flush:flushProposal,reset:resetProposalAutosave,
 edit(text){proposalDraft.summary=text;markProposalChanged();},
 existing(){proposalDraft={id:'proposal',revision:1,status:'draft',summary:'Viewed draft'};resetProposalAutosave();},
 remote(revision){proposalRemote={id:'proposal',revision};},expire(){sessionExpired=true;},resume(){sessionExpired=false;},
 saved(){return {draft:proposalDraft,dirty,error:proposalSaveError,edit:proposalEditVersion,saved:proposalSavedVersion,state};}};`,context);
 return context.controls;
}
async function run(){
 let release;const calls=[];
 const c=setup(async(path,body)=>{calls.push(structuredClone(body.proposal));if(calls.length===1)return new Promise(resolve=>release=resolve);return {proposal:{...body.proposal,id:'proposal',revision:2,progress:{percent:30}}};});
 c.edit('First draft without title');const first=c.flush();assert.equal(calls.length,1);
 c.edit('Typed while first save pending');release({proposal:{...calls[0],id:'proposal',revision:1,progress:{percent:20}}});await first;
 assert.equal(calls.length,2);assert.equal(calls[1].summary,'Typed while first save pending');assert.equal(calls[1].revision,1);
 assert.equal(c.saved().draft.summary,'Typed while first save pending');assert.equal(c.saved().dirty,false);assert.equal(c.saved().draft.revision,2);
 assert.equal(calls[0].creation_key,'12345678-1234-4234-8234-123456789012');assert.equal(calls[0].creation_key,calls[1].creation_key);
 await c.flush();assert.equal(calls.length,2);
 const failed=setup(async()=>{throw Error('Offline');});failed.existing();failed.edit('Keep unsaved text');await assert.rejects(failed.flush(),/Offline/);
 assert.equal(failed.saved().draft.summary,'Keep unsaved text');assert.equal(failed.saved().draft.revision,1);assert.equal(failed.saved().dirty,true);
 const conflict=setup(async()=>{throw Error('Must not send stale draft');});conflict.existing();conflict.edit('Local edits');conflict.remote(2);
 await assert.rejects(conflict.flush(),/Another committee member/);assert.equal(conflict.saved().draft.revision,1);
 let saves=0;const expired=setup(async(path,body)=>{saves++;return {proposal:{...body.proposal,id:'proposal',revision:2}};});expired.existing();expired.edit('Recover this');expired.expire();
 await assert.rejects(expired.flush(),/Session expired/);assert.equal(saves,0);assert.equal(expired.saved().draft.summary,'Recover this');
 expired.resume();await expired.flush();assert.equal(saves,1);assert.equal(expired.saved().dirty,false);
 const retries=[];const replay=setup(async(path,body)=>{retries.push(structuredClone(body.proposal));return {proposal:{...body.proposal,id:'replayed',revision:retries.length},creation_replayed:retries.length===1};});
 replay.edit('Retained after lost create reply');await replay.flush();assert.equal(retries.length,2);assert.equal(retries[1].id,'replayed');assert.equal(retries[1].summary,'Retained after lost create reply');assert.equal(replay.saved().dirty,false);
 console.log('PASS: actual proposal autosave serializes revisions, retains edits during saves/failures, accepts partial drafts, rejects unseen changes and preserves session-expired entries until recovery.');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
