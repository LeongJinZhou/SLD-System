'use strict';
// Executes actual signature controllers with pointer/DOM mocks; no browser-layout claim.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('web/app.js','utf8');
const loader=require('./helpers/source_loader').createSourceLoader(source);
const helpers=loader.section('PROPOSAL_SIGNATURE');
const functions=loader.functions(['proposalReviewMarkup','proposalCanSubmit']);
const requests=[],notices=[];let focused=0,actionPromise;
const error={hidden:true,textContent:''},attributes=new Map(),clearButton={},returnButton={},comment={value:'',setCustomValidity(){},reportValidity(){}};
const canvas={width:1000,height:300,getContext:()=>({beginPath(){},moveTo(){},lineTo(){},stroke(){},clearRect(){}}),getBoundingClientRect:()=>({left:0,top:0,width:1000,height:300}),setPointerCapture(){},setAttribute:(k,v)=>attributes.set(k,v),removeAttribute:k=>attributes.delete(k),focus:()=>focused++,toDataURL:()=> 'data:image/png;base64,drawn-png'};
const form={elements:{review_comment:comment},querySelector:selector=>selector==='canvas'?canvas:selector==='.error-text'?error:selector==='[data-clear-drawing]'?clearButton:returnButton};
const state={user:{email:'advisor@qiu.edu.my',name:'Trusted Advisor',role:'advisor'},clubs:[{id:'club',name:'Approved Club',advisor_email:'advisor@qiu.edu.my',committee:[{email:'president@qiu.edu.my',position:'President'}]}]};
const context=vm.createContext({state,Math,Error,structuredClone,e:value=>String(value??''),requiredLabel:value=>value,localTime:value=>value,proposalCanEdit:p=>p.can_edit,proposalClub:p=>state.clubs.find(club=>club.id===p.club_id),textfield:()=>'<textarea name="review_comment"></textarea>',api:async(path,body)=>{requests.push({path,body});return {proposal:{id:'p',status:'pending_sld'}};},refresh:async()=>{},render:()=>{},notice:value=>notices.push(value),flushProposal:async()=>{},confirmSldSubmission:async()=>true,action:fn=>actionPromise=fn()});
vm.runInContext(`let proposalRemote=null,proposalDraft=null,dirty=false;${helpers}\n${functions}\nglobalThis.controls={draw:wireDrawnSignature,review:wireProposalStageReview,identity:signerIdentityMarkup,slots:proposalSignerBlocks,markup:proposalReviewMarkup,canSubmit:proposalCanSubmit,remote:value=>proposalRemote=value};`,context);
function stroke(){canvas.onpointerdown({clientX:20,clientY:20,pointerId:1,button:0,preventDefault(){}});canvas.onpointermove({clientX:60,clientY:40});canvas.onpointermove({clientX:90,clientY:70});canvas.onpointerup();}
async function run(){
 const c=context.controls,read=c.draw(form);assert.equal(read(),null);assert.equal(attributes.get('aria-invalid'),'true');assert.ok(error.textContent.includes('Draw your signature'));
 canvas.onpointerdown({clientX:20,clientY:20,pointerId:1,button:0,preventDefault(){}});canvas.onpointerup();assert.equal(read(),null,'A click alone must not count as signing');
 stroke();assert.ok(read().startsWith('data:image/png'));clearButton.onclick();assert.equal(read(),null,'Clearing must remove signature validity');
 const identity=c.identity({name:'Profile Name',designation:'President',department:'Approved Club'});assert.ok(identity.includes('Profile Name'));assert.ok(!/<input|<textarea|type="date"/.test(identity));assert.ok(identity.includes('Recorded by the server after signing'));
 const record={id:'p',club_id:'club',status:'pending_advisor',revision:8};const markup=c.markup(record);assert.ok(markup.includes('Club Advisor'));assert.ok(markup.includes('Unavailable'));assert.ok(!markup.includes('Create typed signature'));
 const slots=c.slots({signatures:{preparer:{name:'President',designation:'President',department:'Approved Club',revision:7,signed_at:'immutable-server-time',signature:'data:image/png;base64,drawn'}}});assert.ok(slots.includes('immutable-server-time'));assert.ok(slots.includes('>7</dd>'));assert.ok(slots.includes('Awaiting advisor signature'));assert.ok(slots.includes('Awaiting SLD signature'));
 c.review({querySelector:()=>form},record);form.onsubmit({preventDefault(){}});await actionPromise;assert.equal(requests.length,0,'Blank signature must not reach API');stroke();form.onsubmit({preventDefault(){}});await actionPromise;assert.equal(requests.length,1);assert.equal(requests[0].path,'/api/proposals/p/review');assert.equal(requests[0].body.revision,8);assert.equal(requests[0].body.name,undefined);assert.equal(requests[0].body.date,undefined);assert.ok(requests[0].body.signature.startsWith('data:image/png'));assert.equal(requests[0].body.confirm_submission,true);
 c.remote({revision:9});form.onsubmit({preventDefault(){}});await assert.rejects(actionPromise,/newer proposal/);assert.equal(requests.length,1);
 state.user={email:'president@qiu.edu.my',role:'student'};assert.equal(c.canSubmit({club_id:'club',can_edit:true}),true);state.user={email:'sld@qiu.edu.my',role:'sld'};assert.equal(c.canSubmit({club_id:'club',can_edit:true}),false);
 const draft={id:'p',revision:1,title:'Keep text',history:[{signature:'private'}],signatures:{preparer:{signature:'private'}},signed_versions:[{signature:'private'}],preparer_profile:{name:'private'},reviewer_profile:{name:'private'}};
 let sent;
 const payloadContext=vm.createContext({draft,structuredClone,clearTimeout(){},document:{querySelector:()=>null},captureProposal(){},proposalCanEdit:()=>true,updateProposalProgress(){},api:async(_path,body)=>{sent=body.proposal;return {proposal:{id:'p',revision:2}};}});
 vm.runInContext(`let proposalDraft=draft,dirty=true,state={proposals:[]};${loader.section('PROPOSAL_AUTOSAVE')}\nproposalEditVersion=1;globalThis.saving=flushProposal();`,payloadContext);
 await payloadContext.saving;assert.equal(sent.title,'Keep text');assert.ok(!JSON.stringify(sent).includes('private'));
 const recoveryFields=loader.declaration('const','recoveryProposalFields');vm.runInContext(recoveryFields+'globalThis.fields=recoveryProposalFields;',payloadContext);for(const key of ['signatures','signed_versions','history','signature'])assert.ok(!payloadContext.fields.includes(key));
 console.log('PASS: actual proposal signature controller rejects blank/click drawings, clears strokes, uses readonly identities/server dates and canonical revision slots, protects newer versions and excludes signature data from autosave/recovery.');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
