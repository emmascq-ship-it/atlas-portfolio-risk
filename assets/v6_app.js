(function(){'use strict';
const $=id=>document.getElementById(id);
const money=v=>'$'+Number(v).toLocaleString('en-US',{maximumFractionDigits:0});
const pct=(x,n=1)=>(100*x).toFixed(n)+'%';
const assets=Object.keys(DATA.inputs.weights);
const colors={mint:'#237d73',blue:'#377cf6',red:'#b44e50',amber:'#c79b5c',grid:'#edf0f5',muted:'#526078'};
const baseLayout=(height=310,extras={})=>Object.assign({height,margin:{l:46,r:18,t:12,b:47},font:{family:'-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif',size:12,color:colors.muted},paper_bgcolor:'#fff',plot_bgcolor:'#fff',xaxis:{gridcolor:colors.grid,zeroline:false},yaxis:{gridcolor:colors.grid,zeroline:false}},extras);
const cfg={responsive:true,displayModeBar:false};

// V7: A genuine, independent forecasting benchmark, not simply two styled series.
const comparison=DATA.benchmark;
const modelA=comparison.models.historical,modelB=comparison.models.gaussian;
const diagRows=[
 ['Out-of-sample forecasts',x=>String(x.observations)],
 ['Observed VaR breaches',x=>String(x.breaches)],
 ['Expected exceptions',x=>x.expected_breaches.toFixed(1)],
 ['Empirical hit rate',x=>pct(x.observed_breach_rate,2)],
 ['Kupiec p-value',x=>x.kupiec_p_approx.toFixed(3)],
 ['Conditional coverage p',x=>x.conditional_p_approx.toFixed(3)],
 ['Max consecutive breaches',x=>String(x.max_consecutive_breaches)],
 ['Mean exceedance over VaR',x=>pct(x.mean_breach_excess,3)],
 ['Worst exceedance over VaR',x=>pct(x.worst_breach_excess,3)],
];
for(const [label,fmt] of diagRows){const tr=document.createElement('tr');for(const value of [label,fmt(modelA),fmt(modelB)]){const td=document.createElement('td');td.textContent=value;tr.appendChild(td)}$('benchmark_rows').appendChild(tr)}
$('benchmark_warnings').textContent=([modelA,modelB].flatMap(x=>x.warnings).filter((v,i,a)=>a.indexOf(v)===i).join(' • ') || 'No rare-event warning at the displayed confidence level.')+'  A non-significant test does not prove safety or regulatory compliance.';
Plotly.newPlot('benchmark_chart',[
 {x:comparison.dates,y:comparison.realized.map(x=>x*100),type:'scatter',mode:'lines',line:{color:'#99a6b7',width:1},name:'Realized daily loss'},
 {x:comparison.dates,y:comparison.historical.map(x=>x*100),type:'scatter',mode:'lines',line:{color:colors.blue,width:1.8},name:'Historical VaR'},
 {x:comparison.dates,y:comparison.gaussian.map(x=>x*100),type:'scatter',mode:'lines',line:{color:colors.mint,width:1.8},name:'Gaussian VaR'},
],baseLayout(310,{yaxis:{title:{text:'Loss / forecast (%)',font:{size:11}},gridcolor:colors.grid},legend:{orientation:'h',y:-.28,font:{size:9}},margin:{l:55,r:10,t:10,b:75}}),cfg);
$('benchmarkdownload').addEventListener('click',()=>{const lines=['Date,Realized Loss,Historical VaR,Gaussian VaR'];for(let i=0;i<comparison.dates.length;i++){lines.push([comparison.dates[i],comparison.realized[i],comparison.historical[i],comparison.gaussian[i]].join(','))}download('atlas_var_benchmark_UNAPPROVED.csv',lines.join('\n')+'\n','text/csv')});


// A separate dataset-quality inventory. These are descriptive flags, not compliance approval.
const q=DATA.quality;
const qualityRows=[['Input validation',q.input_controls_passed+' / '+q.input_controls_total+' checks'],
 ['Portfolio history',q.records.toLocaleString('en-US')+' sessions'],
 ['Tracked assets',String(q.assets)],
 ['Last observation',q.last_date],
 ['Snapshot age',q.synthetic_snapshot_assessment?'Archived synthetic assessment as of '+q.assessment_as_of+' (not current market data)':q.days_since_last_observation+' calendar days'],
 ['Large weekday gaps',String(q.large_weekday_gap_count)],
 ['Largest daily asset move',pct(q.largest_absolute_daily_asset_return,2)]];
for(const [key,val] of qualityRows){const cell=document.createElement('div'),name=document.createElement('b');name.textContent=key+' ';cell.append(name,document.createTextNode(val));$('data_quality').appendChild(cell)}
$('quality_flags').textContent=q.review_flags.join(' • ');

$('snapshot-meta').textContent=DATA.period.join(' – ')+'  ·  '+DATA.quality.records+' price dates / '+DATA.growth.dates.length+' daily returns  ·  '+DATA.quality.input_controls_passed+' / '+DATA.quality.input_controls_total+' input checks passed  ·  Static demo / USD';
$('hero-notional').textContent=money(DATA.inputs.notional);
$('hero-range').textContent=DATA.growth.dates.length.toLocaleString('en-US')+' days';
const d=DATA.drawdown;
Plotly.newPlot('drawdown_chart',[{x:d.dates,y:d.values.map(x=>x*100),type:'scatter',mode:'lines',name:'Drawdown',fill:'tozeroy',fillcolor:'rgba(200,84,105,.12)',line:{color:colors.red,width:1.7},hovertemplate:'%{x}<br>Drawdown: %{y:.2f}%<extra></extra>'}],baseLayout(285,{yaxis:{title:{text:'Drawdown (%)',font:{size:11}},gridcolor:colors.grid,zeroline:true,zerolinecolor:'#b8c9d4'}}),cfg);
const r=assets.map(a=>DATA.asset_vol[a]*100);
Plotly.newPlot('risk_contrib_chart',[{x:r,y:assets,type:'bar',orientation:'h',marker:{color:r.map(x=>x<0?colors.red:colors.blue)},hovertemplate:'%{y}: %{x:.2f} percentage points<extra></extra>'}],baseLayout(285,{margin:{l:110,r:15,t:10,b:35},xaxis:{title:{text:'Annualized vol contribution (pp)',font:{size:11}},gridcolor:colors.grid},yaxis:{autorange:'reversed'}}),cfg);
const cor=DATA.correlations;
Plotly.newPlot('correlation',[{z:cor.values,x:cor.assets,y:cor.assets,type:'heatmap',zmin:-1,zmax:1,zmid:0,colorscale:[[0,'#c95e75'],[.5,'#f4f7fa'],[1,'#377cf6']],showscale:true,colorbar:{len:.72,thickness:9,outlinewidth:0,tickfont:{size:9}},hovertemplate:'%{y} / %{x}<br>Correlation: %{z:.2f}<extra></extra>'}],baseLayout(390,{margin:{l:94,r:7,t:20,b:90},xaxis:{side:'bottom',tickangle:-43,tickfont:{size:9}},yaxis:{autorange:'reversed',tickfont:{size:9}}}),cfg);
for(const asset of assets){const tr=document.createElement('tr'),td1=document.createElement('td'),td2=document.createElement('td'),td3=document.createElement('td'),w=DATA.inputs.weights[asset];td1.textContent=asset;td2.textContent=DATA.inputs.asset_class[asset];const track=document.createElement('span');track.className='weight-track';const bar=document.createElement('span');bar.className='weight-bar';bar.style.width=(w/Math.max(...Object.values(DATA.inputs.weights))*100).toFixed(3)+'%';track.appendChild(bar);td3.appendChild(track);td3.appendChild(document.createTextNode(pct(w,1)));tr.append(td1,td2,td3);$('positions').appendChild(tr)}
const presetDiv=$('presets');
const presets=DATA.scenario_presets;
const fields=()=>Object.fromEntries([...document.querySelectorAll('#shockfields input')].map(i=>[i.dataset.category,i.value.trim()===''?NaN:Number(i.value)/100]));
const currentContrib=sh=>assets.map(a=>({asset:a,asset_class:DATA.inputs.asset_class[a],weight:DATA.inputs.weights[a],shock:sh[DATA.inputs.asset_class[a]],contribution:DATA.inputs.weights[a]*sh[DATA.inputs.asset_class[a]]}));
const scenarioTotal=sh=>currentContrib(sh).reduce((acc,c)=>acc+c.contribution,0);
const triggerInput=(sh)=>{for(const key of DATA.inputs.classes){const el=[...document.querySelectorAll('#shockfields input')].find(i=>i.dataset.category===key);if(!el)throw Error('Missing shock editor for '+key);el.value=(sh[key]*100).toFixed(2);el.dispatchEvent(new Event('input',{bubbles:true}))}};
for(const [name,sh] of Object.entries(presets)){const b=document.createElement('button');b.className='preset';b.textContent=name;b.type='button';b.dataset.preset=name;b.addEventListener('click',()=>{triggerInput(sh);updatePresetState()});presetDiv.appendChild(b)}
function updatePresetState(){const curr=fields();for(const b of presetDiv.querySelectorAll('button')){const sh=presets[b.dataset.preset];const selected=DATA.inputs.classes.every(k=>Math.abs(curr[k]-sh[k])<.000051);b.classList.toggle('active',selected);b.setAttribute('aria-pressed',String(selected))}}
const names=Object.keys(presets),values=names.map(n=>scenarioTotal(presets[n])*100);
Plotly.newPlot('scenario_compare',[{x:values,y:names,type:'bar',orientation:'h',marker:{color:values.map(v=>v<0?colors.red:colors.mint)},hovertemplate:'%{y}: %{x:.3f}%<extra></extra>'}],baseLayout(310,{margin:{l:110,r:22,t:15,b:45},xaxis:{title:{text:'Portfolio impact (%)',font:{size:11}},gridcolor:colors.grid,zeroline:true,zerolinecolor:'#bbc9d2'},yaxis:{autorange:'reversed'}}),cfg);
$('shockfields').addEventListener('input',updatePresetState);
$('reset').addEventListener('click',()=>requestAnimationFrame(updatePresetState));
updatePresetState();
const download=(filename,text,type)=>{const blob=new Blob([text],{type});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.download=filename;a.href=url;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)};
const buildScenarioExport=()=>{const sh=fields();if(Object.values(sh).some(v=>!Number.isFinite(v)||v< -1||v>2)){throw Error('Scenario shocks must be valid numbers between -100% and +200%')}const cs=currentContrib(sh);return {schema:'atlas-risk-scenario-v1',approval_status:'UNAPPROVED_HYPOTHETICAL',market_data_source:DATA.source,synthetic:DATA.synthetic,baseline_scenario:DATA.inputs.scenario,baseline_input_sha256:DATA.inputs.saved_input_sha256,confidence:DATA.inputs.confidence,portfolio_notional_usd:DATA.inputs.notional,asset_weights:DATA.inputs.weights,class_shocks:sh,portfolio_return:scenarioTotal(sh),portfolio_pnl_usd:scenarioTotal(sh)*DATA.inputs.notional,asset_contributions:cs,assumptions:['Instantaneous class-level shocks','Fixed target weights','No transaction costs, market impact or scenario probability','Edited scenarios do not re-run VaR or change historical evidence','No approval or signature']}};
$('scenarioexport').addEventListener('click',()=>{try{download('atlas_scenario_UNAPPROVED.json',JSON.stringify(buildScenarioExport(),null,2),'application/json')}catch(err){alert(err.message)}});
$('scenarioexportcsv').addEventListener('click',()=>{let cs;try{cs=buildScenarioExport().asset_contributions}catch(err){alert(err.message);return;} const rows=['Asset,Asset class,Weight,Class shock,Return contribution,USD P&L'];for(const c of cs)rows.push([c.asset,c.asset_class,c.weight,c.shock,c.contribution,c.contribution*DATA.inputs.notional].join(','));download('atlas_scenario_contributions_UNAPPROVED.csv',rows.join('\n')+'\n','text/csv')});
const tabs=[...document.querySelectorAll('.tab')];tabs.forEach((tab,i)=>tab.addEventListener('keydown',ev=>{let next=-1;if(ev.key==='ArrowDown'||ev.key==='ArrowRight')next=(i+1)%tabs.length;else if(ev.key==='ArrowUp'||ev.key==='ArrowLeft')next=(i-1+tabs.length)%tabs.length;else if(ev.key==='Home')next=0;else if(ev.key==='End')next=tabs.length-1;if(next>=0){ev.preventDefault();tabs[next].focus();tabs[next].click()}}));
// Keep page context and accessible panel names aligned with the selected module.
const moduleContext={overview:['Portfolio overview','Portfolio risk, allocation and historical behavior for the saved research snapshot.'],factors:['Factor exposures','Inspect descriptive ETF-spread sensitivities and regression limitations.'],scenario:['Scenario laboratory','Explore transparent hypothetical shocks; edited results remain unapproved.'],validation:['Model validation','Compare rolling forecasts, exception coverage and model diagnostics.'],review:['Research review desk','Inspect evidence, source provenance and the unapproved research draft.']};
for(const tab of tabs){tab.id='tab-'+tab.dataset.target;tab.tabIndex=tab.classList.contains('active')?0:-1;const panel=$(tab.dataset.target);panel.setAttribute('aria-labelledby',tab.id);tab.addEventListener('click',()=>{const context=moduleContext[tab.dataset.target];$('workspace-title').textContent=context[0];$('workspace-description').textContent=context[1];});}
// Resize cached Plotly instances after hidden panels become visible.
for(const tab of tabs){tab.addEventListener('click',()=>setTimeout(()=>{for(const el of document.querySelectorAll('#'+tab.dataset.target+' .js-plotly-plot')){try{Plotly.Plots.resize(el)}catch(_){}}},100))}
})();
