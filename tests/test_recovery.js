'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('web/app.js','utf8'),start=source.indexOf('const recoveryClubFields='),end=source.indexOf('function showSessionExpired()',start);
assert.ok(start>=0&&end>start);
const values=new Map(),notices=[];
const context=vm.createContext({structuredClone,Error,JSON,sessionStorage:{setItem:(k,v)=>values.set(k,v),getItem:k=>values.get(k),removeItem:k=>values.delete(k)},
 captureClub:()=>{},captureProposal:()=>{},notice:msg=>notices.push(msg),clubCanEditProposals:c=>Boolean(c?.can_edit_proposals),
 resetAutosave:()=>{},resetProposalAutosave:()=>{}});
vm.runInContext(`let state={user:{id:'one',email:'one@qiu.edu.my'},clubs:[{id:'club',revision:2,status:'approved',can_edit:false,can_edit_proposals:true,history:[]}],proposals:[{id:'p',revision:2,status:'draft',can_edit:true,history:[]}]};
 let clubDraft={id:'club',revision:1,bio:'Unsaved biography',history:[{signature:'private-signature'}],csrf:'do-not-cache',can_edit:true},
 proposalDraft={id:'p',revision:1,club_id:'club',summary:'Unsaved proposal',history:[{signature:'private-signature'}],token:'do-not-cache',can_edit:true},
 recoveryOwner={id:'old',email:'old@qiu.edu.my'},sessionExpired=false,dirty=true,view='proposals',proposalStep=1,selectedClubId='club',
 clubEditVersion=0,clubSavedVersion=0,proposalEditVersion=0,proposalSavedVersion=0,clubRemote=null,proposalRemote=null,clubSaveError='',proposalSaveError='';
 const recoveryKey='test';
 ${source.slice(start,end)}
 globalThis.controls={persistRecovery,clearRecovery,restoreRecovery,
 setUser(id,email){state.user={id,email};},clearDrafts(){clubDraft=proposalDraft=null;},
 removeAccess(){state.clubs=[];state.proposals=[];},
 snapshot(){return {owner:recoveryOwner,club:clubDraft,proposal:proposalDraft,clubRemote,proposalRemote,dirty};}};`,context);
const c=context.controls;
assert.equal(c.persistRecovery(),true);
const cached=JSON.parse(values.get('test'));assert.equal(cached.owner.id,'one');
assert.equal(cached.club.history,undefined);assert.equal(cached.club.csrf,undefined);assert.equal(cached.club.can_edit,undefined);
assert.equal(cached.proposal.history,undefined);assert.equal(cached.proposal.token,undefined);
c.clearDrafts();c.setUser('other','other@qiu.edu.my');assert.equal(c.restoreRecovery(),false);assert.equal(c.snapshot().proposal,null);
c.setUser('one','one@qiu.edu.my');assert.equal(c.restoreRecovery(),true);
assert.equal(c.snapshot().proposal.summary,'Unsaved proposal');assert.equal(c.snapshot().proposal.revision,1);assert.equal(c.snapshot().proposalRemote.revision,2);
assert.equal(c.snapshot().club.can_edit,false);assert.equal(c.snapshot().clubRemote.revision,2);
c.removeAccess();assert.equal(c.restoreRecovery(),true);assert.equal(c.snapshot().proposal.can_edit,false);assert.equal(c.snapshot().proposal.status,'unavailable');
c.clearRecovery();assert.equal(c.snapshot().owner,null);assert.equal(values.has('test'),false);
console.log('PASS: actual recovery strips signatures/tokens/permissions, isolates account identity, preserves draft text, rechecks both revisions/access and clears stale owner state.');
