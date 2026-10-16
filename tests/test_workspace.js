'use strict';
// Real controller helpers with a DOM mock; does not claim browser layout QA.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('web/app.js','utf8');
const scroll=source.slice(source.indexOf('// WORKSPACE_SCROLL_START'),source.indexOf('// WORKSPACE_SCROLL_END'));
const functions=['workspaceKind','performanceCanView','performanceClubs','navigationGroups','reviewAssignments','markNotificationRead','openNotificationRecord'].map(name=>source.split(/\r?\n/).find(line=>line.startsWith(`function ${name}(`)||line.startsWith(`async function ${name}(`))).join('\n');
const details=[{open:true},{open:false}],focus=[],moves=[],requests=[],renders=[];
const input={id:'objective_0',name:'objective_0',tagName:'INPUT',dataset:{},selectionStart:3,selectionEnd:7,focus:options=>focus.push(options),setSelectionRange:(start,end)=>{input.range=[start,end];}};
const main={focus:options=>focus.push(options)},form={querySelectorAll:()=>details};
const document={activeElement:input,querySelector:selector=>selector==='form'?form:main,querySelectorAll:()=>[input]};
const context=vm.createContext({document,window:{scrollX:0,scrollY:840,scrollTo:position=>moves.push(position)},Number,Array,JSON,Error,structuredClone,
  api:async(path,body)=>{requests.push({path,body});return {unread_count:2,notification:{id:'notice',read_at:'server-time'}};},
  updateNotificationBadge:()=>{},leaveCurrent:async()=>{},refresh:async()=>{},resetProposalAutosave:()=>{},resetAutosave:()=>{},render:options=>renders.push(options),
  visibleClubs:()=>context.state.clubs,visibleProposals:()=>context.state.proposals,proposalClub:proposal=>context.state.clubs.find(club=>club.id===proposal.club_id),
  state:{user:{role:'student',email:'student@qiu.edu.my'},clubs:[],proposals:[],notifications_unread_count:3}});
vm.runInContext(`let clubDraft=null,clubProfile=null,proposalDraft=null,financeDraft=null,financeEventId=null,proposalStep=0,view='notifications';${scroll}\n${functions}\nglobalThis.controls={capture:captureUiPosition,restore:restoreUiPosition,kind:workspaceKind,groups:navigationGroups,reviews:reviewAssignments,read:markNotificationRead,open:openNotificationRecord,current:()=>({proposalDraft,view})};`,context);
async function run(){
 const c=context.controls,position=c.capture();details[0].open=false;details[1].open=true;c.restore(position);
 assert.equal(moves.at(-1).top,840);assert.equal(focus.at(-1).preventScroll,true);assert.deepEqual(input.range,[3,7]);assert.equal(details[0].open,true);assert.equal(details[1].open,false);
 c.restore(position,{resetScroll:true,preserveFocus:false});assert.equal(moves.at(-1).top,0);
 assert.equal(c.kind(),'student');assert.ok(!JSON.stringify(c.groups('student')).includes('Review queue'));
 context.state.user={role:'advisor',email:'advisor@qiu.edu.my'};context.state.clubs=[{id:'a',advisor_email:'advisor@qiu.edu.my',status:'pending_advisor'},{id:'b',advisor_email:'other@qiu.edu.my',status:'pending_advisor'}];
 context.state.proposals=[{id:'p',club_id:'a',status:'pending_advisor'},{id:'q',club_id:'b',status:'pending_advisor'}];
 assert.equal(c.kind(),'advisor');assert.equal(c.reviews().clubs.length,1);assert.equal(c.reviews().proposals.length,1);
 context.state.user.role='sld';assert.ok(JSON.stringify(c.groups('sld')).includes('University contacts'));assert.ok(JSON.stringify(c.groups('sld')).includes('Settings'));
 await c.read('notice');assert.equal(context.state.notifications_unread_count,2);assert.equal(requests.at(-1).path,'/api/notifications/notice/read');
 await c.open({id:'notice',record_type:'proposal',record_id:'p'});assert.equal(c.current().view,'proposals');assert.equal(c.current().proposalDraft.id,'p');assert.equal(renders.at(-1).resetScroll,true);
 await assert.rejects(c.open({id:'revoked',record_type:'proposal',record_id:'missing'}),/current assignment/);
 console.log('PASS: actual scroll helper restores viewport/focus/selection/disclosures, deliberate navigation resets, role queues are scoped and notification read/open controllers reject unavailable records.');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
