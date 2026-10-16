'use strict';
// Pure Node checks of the actual save controller; no browser access or UI claims.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('web/app.js','utf8');
const start=source.indexOf('let clubEditVersion=');
const end=source.indexOf('function progressMarkup',start);
assert.ok(start>=0&&end>start);
const controller=source.slice(start,end);
const polling=source.slice(source.indexOf('function startPolling()'),source.indexOf('function updateProgress()'));
function setup(api){
 let tick;const readers=[];
 const context=vm.createContext({structuredClone,Error,clearTimeout:()=>{},setTimeout:()=>1,api,
  setInterval:fn=>{tick=fn;return 1;},clearInterval:()=>{},updateProgress:()=>{},showRemoteChange:()=>{},updateDashboardQueues:()=>{},render:()=>{},
  FileReader:class{readAsDataURL(){readers.push(this);}},
  document:{querySelector:()=>null},captureClub:()=>{},notice:()=>{},canLeave:()=>false});
 vm.runInContext(`let state={user:{role:'student'},clubs:[],registration_grants:[{id:'grant',status:'available'}]},dirty=false,busy=false,view='clubs';
 let clubDraft={registration_grant_id:'grant',bio:'First entry'};
 ${controller}
 ${polling}
 globalThis.controls={flushClub,leaveCurrent,markClubChanged,resetAutosave,
 baseline(){clubDraft={id:'club',revision:1,bio:'Previously viewed content'};resetAutosave();},startPolling,
 readLogo(){return readClubLogo({target:{files:[{size:100,type:'image/png'}],isConnected:true}},clubDraft);},
 edit(value){clubDraft.bio=value;markClubChanged();}, lock(){clubDraft.sld_review_started_at='now';},
 saved(){return {club:clubDraft,dirty,editVersion:clubEditVersion,savedVersion:clubSavedVersion,error:clubSaveError,state,remote:clubRemote};}};`,context);
 context.controls.tick=()=>tick();
 context.controls.finishLogo=value=>{const reader=readers.shift();reader.result=value;reader.onload();};
 context.controls.failLogo=()=>readers.shift().onerror();
 return context.controls;
}
async function run(){
 const calls=[];let resolveFirst;
 const c=setup(async(path,body)=>{
  calls.push(structuredClone(body.club));
  if(calls.length===1)return new Promise(resolve=>resolveFirst=resolve);
  return {club:{...body.club,id:'club',revision:2,can_edit:true}};
 });
 c.edit('First entry');const pending=c.flushClub();
 assert.equal(calls.length,1);
 c.edit('Typed while saving');resolveFirst({club:{...calls[0],id:'club',revision:1,can_edit:true}});
 await pending;
 assert.equal(calls.length,2);assert.equal(calls[1].bio,'Typed while saving');assert.equal(calls[1].revision,1);
 assert.equal(c.saved().club.bio,'Typed while saving');assert.equal(c.saved().dirty,false);
 assert.equal(c.saved().state.registration_grants[0].status,'used');
 await c.leaveCurrent();assert.equal(c.saved().dirty,false);
 const failing=setup(async()=>{throw Error('Offline');});failing.edit('Keep this entry');
 await assert.rejects(failing.leaveCurrent(),/Offline/);
 assert.equal(failing.saved().club.bio,'Keep this entry');assert.equal(failing.saved().dirty,true);
 assert.equal(failing.saved().error,'Offline');
 let saves=0;const locked=setup(async()=>{saves++;});locked.edit('Cannot write');locked.lock();
 await assert.rejects(locked.flushClub(),/SLD has started reviewing/);assert.equal(saves,0);
 const shared=setup(async()=>({user:{role:'student'},clubs:[{id:'club',revision:2,bio:'Another member changed this',progress:{percent:80}}]}));
 shared.baseline();shared.startPolling();await shared.tick();
 assert.equal(shared.saved().club.revision,1);assert.equal(shared.saved().club.bio,'Previously viewed content');
 assert.equal(shared.saved().remote.revision,2);
 shared.edit('My later edit');await assert.rejects(shared.flushClub(),/Load its latest saved version/);
 assert.equal(shared.saved().club.revision,1);
 let logoSaves=[];const logo=setup(async(path,body)=>{logoSaves.push(body.club);return {club:{...body.club,id:'club',revision:1}};});
 const reading=logo.readLogo(),leaving=logo.leaveCurrent();assert.equal(logoSaves.length,0);
 logo.finishLogo('data:image/png;base64,test');await Promise.all([reading,leaving]);
 assert.equal(logoSaves[0].logo,'data:image/png;base64,test');assert.equal(logo.saved().dirty,false);
 const badLogo=setup(async()=>{throw Error('Must not save unread logo');});
 const failureResults=Promise.allSettled([badLogo.readLogo(),badLogo.leaveCurrent()]);badLogo.failLogo();
 assert.ok((await failureResults).every(result=>result.status==='rejected'));assert.equal(badLogo.saved().dirty,true);
 console.log('PASS: serialized autosave retains in-flight edits, updates revision, consumes local invitation, flushes navigation, preserves failed saves, rejects locked saves and does not adopt unseen remote revisions.');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
