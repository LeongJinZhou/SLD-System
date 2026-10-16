'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('web/app.js','utf8'),names=['humanDate','humanPeriod','financeChart','progressChart','financeHeatmap','financeLedger','activitySummaryMarkup','loadClubFinance'];
const loader=require('./helpers/source_loader').createSourceLoader(source);
const functions=loader.functions(names);
const target={innerHTML:'',querySelectorAll:()=>[],querySelector:()=>null},main={isConnected:true,querySelector:()=>target};
const fixture={balance:'75.00',approved_income:'100.00',approved_expenses:'25.00',opening_balance:'0.00',opening_set:false,monthly:[{period:'2026-10',income:'100.00',expenses:'25.00',net:'75.00',events:2,actions:3}],activity_days:[{date:'2026-11-22',count:2,event_ids:['event'],actions:[]}],events:[{proposal_id:'event',status:'draft',title:'Learning event',date:'2026-11-22',planned_income:'100.00',planned_expenses:'25.00',actual_income:'100.00',actual_expenses:'25.00',report_status:'approved'}],entries:[{proposal_id:'event',description:'Materials payment',kind:'expense',amount:'25.00',approved_at:'2026-10-08T02:00:00+00:00'}],can_admin:false};
const context=vm.createContext({Date,Map,Math,Array,Number,state:{server_time:'2026-10-08T02:00:00+00:00'},e:value=>String(value??''),money:value=>'MYR '+value,mytParts:()=>({year:'2026'}),statusLabel:value=>value,localTime:value=>value,humanAction:value=>value,wireFinanceHeatmap:()=>{},wireFinanceEventLinks:()=>{},api:async()=>fixture});
vm.runInContext(`let financeHeatmapYear=null,financeRevisionRequest=0,financeData=null,financePeriod='monthly',view='finance';${functions}
 globalThis.controls={heatmap:financeHeatmap,progress:progressChart,load:loadClubFinance,setYear(year){financeHeatmapYear=year;}};`,context);
async function run(){
 const c=context.controls,heat=c.heatmap(fixture.activity_days);assert.equal((heat.match(/data-finance-day=/g)||[]).length,365);assert.ok(heat.includes('22 Nov 2026: 2 club actions or scheduled proposals'));
 c.setYear(2028);assert.equal((c.heatmap([]).match(/data-finance-day=/g)||[]).length,366);
 const progress=c.progress(fixture.monthly);assert.ok(progress.includes('2 approved events'));assert.ok(progress.includes('2 scheduled proposals, all statuses'));assert.ok(progress.includes('3 recorded club actions'));
 await c.load({id:'club',name:'Society'},main);const event=target.innerHTML.match(/<details class="finance-event-record">[\s\S]*?<\/details>/)[0];assert.ok(event.includes('Proposal: draft'));assert.ok(event.includes('Materials payment'));assert.ok(event.includes('MYR 25.00'));assert.ok(!target.innerHTML.includes('Club progress over time'));assert.ok(!target.innerHTML.includes('finance-heatmap'));assert.ok(target.innerHTML.includes('Income & expenses over time'));
 console.log('PASS: actual chart helpers render real counts, future event dates and leap-year cells; expandable event view includes its own approved transactions.');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
