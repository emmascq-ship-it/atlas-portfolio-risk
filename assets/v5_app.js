(function(){'use strict';
const $=id=>document.getElementById(id), pct=(v,d=2)=>(100*v).toFixed(d)+'%', money=v=>(v<0?'−':'')+'$'+Math.abs(v).toLocaleString('en-US',{maximumFractionDigits:0}),c='#377cf6',negative='#b44e50';
const opts={responsive:true,displayModeBar:false};
const layout=(height=320,extras={})=>Object.assign({height,margin:{l:55,r:20,t:12,b:48},font:{family:'-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif',size:12,color:'#526078'},paper_bgcolor:'white',plot_bgcolor:'white',xaxis:{gridcolor:'#edf0f5',zeroline:false},yaxis:{gridcolor:'#edf0f5',zeroline:false}},extras);
const plot=(id,traces,layoutObj)=>Plotly.newPlot(id,traces,layoutObj,opts);
function download(name, content, type){const blob=new Blob([content],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function chartWithRange(id, data, lay){plot(id,data,lay)}
$('sourcetext').textContent=DATA.source;
$('var').textContent=pct(DATA.kpis.var);$('es').textContent=pct(DATA.kpis.es);$('vol').textContent=pct(DATA.kpis.volatility);$('dd').textContent=pct(DATA.kpis.drawdown);
$('overviewnotes').textContent=`${pct(DATA.inputs.confidence,1)} historical confidence · $${DATA.inputs.notional.toLocaleString('en-US')} hypothetical notional · ${DATA.inputs.window}-day rolling backtest window. 1-day VaR ≈ ${money(DATA.kpis.var*DATA.inputs.notional)}; ES ≈ ${money(DATA.kpis.es*DATA.inputs.notional)}. Historical results are not loss guarantees.`;
chartWithRange('growth',[{x:DATA.growth.dates,y:DATA.growth.values,type:'scatter',mode:'lines',line:{color:c,width:2.4},name:'Growth of $1'}],layout(320,{yaxis:{title:{text:'USD index',font:{size:11}},gridcolor:'#edf0f5'}}));
const assets=Object.keys(DATA.inputs.weights), w=assets.map(a=>DATA.inputs.weights[a]*100);
chartWithRange('allocation',[{x:w,y:assets,type:'bar',orientation:'h',marker:{color:'#377cf6'}}],layout(320,{margin:{l:108,r:20,t:12,b:44},xaxis:{title:{text:'Target weight (%)',font:{size:11}},gridcolor:'#edf0f5'},yaxis:{autorange:'reversed'}}));
const f=DATA.factors,fn=Object.keys(f.beta);
chartWithRange('betas',[{y:fn,x:fn.map(x=>f.beta[x]),orientation:'h',type:'bar',marker:{color:fn.map(x=>f.beta[x]<0?negative:c)}}],layout(400,{margin:{l:135,r:25,t:12,b:52},xaxis:{title:{text:'OLS beta',font:{size:11}},gridcolor:'#edf0f5'},yaxis:{autorange:'reversed'}}));
chartWithRange('factorvariance',[{y:fn,x:fn.map(x=>f.variance[x]),orientation:'h',type:'bar',marker:{color:fn.map(x=>f.variance[x]<0?negative:'#377cf6')}}],layout(400,{margin:{l:135,r:25,t:12,b:52},xaxis:{title:{text:'Annualized fitted variance',font:{size:11}},gridcolor:'#edf0f5'},yaxis:{autorange:'reversed'}}));
$('factorinfo').textContent=`In-sample R² ${pct(f.r2,1)} · design condition number ${f.condition.toFixed(1)}. The factors are ETF return spreads constructed from the SAME instruments used in the portfolio. A high fitted R² is mechanically unsurprising and should not be interpreted as predictive accuracy or causal identification.`;
const fields=$('shockfields'), shocks={...DATA.inputs.shocks};
DATA.inputs.classes.forEach(k=>{const item=document.createElement('div');item.className='field';const label=document.createElement('label');label.htmlFor='shock-'+DATA.inputs.classes.indexOf(k);label.textContent=k+' (%)';const input=document.createElement('input');input.type='number';input.id=label.htmlFor;input.name=input.id;input.autocomplete='off';input.min='-100';input.max='200';input.step='0.5';input.value=(100*shocks[k]).toFixed(1);input.dataset.category=k;input.addEventListener('input',()=>{const n=Number(input.value);if(input.value.trim()===''){return;}if(!Number.isFinite(n)||n< -100||n>200){input.value=(100*shocks[k]).toFixed(1);return;}shocks[k]=n/100;updateScenario()});item.append(label,input);fields.appendChild(item)});
function updateScenario(){const contrib=assets.map(a=>DATA.inputs.weights[a]*shocks[DATA.inputs.asset_class[a]]),total=contrib.reduce((a,b)=>a+b,0),largest=contrib.reduce((idx,v,i)=>Math.abs(v)>Math.abs(contrib[idx])?i:idx,0);$('scenario_pct').textContent=(total>=0?'+':'')+pct(total,3);$('scenario_pct').className='value '+(total<0?'warning':'positive');$('scenario_usd').textContent=money(total*DATA.inputs.notional);$('driver').textContent=assets[largest];const changed=DATA.inputs.classes.some(k=>Math.abs(shocks[k]-DATA.inputs.shocks[k])>1e-9);$('scenario_state').textContent=changed?'MODIFIED':'BASELINE';$('scenario_state').className='value '+(changed?'warning':'positive');chartWithRange('scenariochart',[{x:contrib.map(x=>x*100),y:assets,type:'bar',orientation:'h',marker:{color:contrib.map(x=>x<0?negative:c)}}],layout(320,{margin:{l:110,r:25,t:12,b:48},xaxis:{title:{text:'Portfolio return contribution (pp)',font:{size:11}},gridcolor:'#edf0f5',zeroline:true,zerolinecolor:'#b8cbd1'},yaxis:{autorange:'reversed'}}));}
$('reset').addEventListener('click',()=>{DATA.inputs.classes.forEach(k=>{shocks[k]=DATA.inputs.shocks[k];document.querySelector(`[data-category="${k}"]`).value=(100*shocks[k]).toFixed(1)});updateScenario()});
updateScenario();
const b=DATA.backtest,breachX=[],breachY=[];b.breaches.forEach((v,i)=>{if(v){breachX.push(b.dates[i]);breachY.push(b.actual[i]*100)}});
chartWithRange('backtest',[{x:b.dates,y:b.actual.map(v=>v*100),mode:'lines',type:'scatter',name:'Realized loss',line:{color:'#8193a9',width:1.5}},{x:b.dates,y:b.forecast.map(v=>v*100),mode:'lines',type:'scatter',name:'VaR forecast',line:{color:'#c79b5c',width:2}},{x:breachX,y:breachY,mode:'markers',type:'scatter',name:'Breach',marker:{size:7,color:negative}}],layout(400,{yaxis:{title:{text:'Daily loss (%)',font:{size:11}},gridcolor:'#edf0f5'},legend:{orientation:'h',y:-.25}}));
$('breaches').textContent=`${DATA.kpis.breaches} / ${DATA.kpis.backtest_observations}`;$('expected').textContent=DATA.kpis.expected_breaches.toFixed(1);$('kupiec').textContent=DATA.kpis.kupiec_p.toFixed(3);$('christoff').textContent=DATA.kpis.christoffersen_p.toFixed(3);
$('validationnotes').textContent=`Approximate conditional-coverage p-value: ${DATA.kpis.conditional_p.toFixed(3)}. Failing to reject a null is NOT proof of model validity. Rare exceptions can weaken asymptotic tests; intraday, liquidity and model regime risks are not captured.`;
// Build a narrow Markdown preview using text nodes, never HTML from report content.
// The immutable original Markdown is still the download and evidence source.
function reportPreview(target, markdown){
 let list=null;
 const inline=(node,text)=>{text.split(/(\*\*[^*]+\*\*)/g).forEach(part=>{if(part.startsWith('**')&&part.endsWith('**')){const strong=document.createElement('strong');strong.textContent=part.slice(2,-2);node.appendChild(strong)}else node.appendChild(document.createTextNode(part))})};
 for(const line of markdown.split('\n')){
  if(!line.trim()){list=null;continue;}
  const heading=line.match(/^(#{1,3}) (.*)$/),bullet=line.match(/^- (.*)$/);
  if(bullet){if(!list){list=document.createElement('ul');target.appendChild(list)}const li=document.createElement('li');inline(li,bullet[1]);list.appendChild(li);continue;}
  list=null;const el=document.createElement(heading?(heading[1].length===1?'h2':'h3'):'p');inline(el,heading?heading[2]:line);target.appendChild(el);
 }
}
reportPreview($('brief'),DATA.review.draft);for(const [k,v] of Object.entries(DATA.review.evidence)){const d=document.createElement('div');const b=document.createElement('b');b.textContent=k;d.append(b,document.createTextNode(v));$('evidence').appendChild(d)}$('fingerprint').textContent='Original unrounded input SHA-256: '+DATA.inputs.saved_input_sha256;
const ul=document.createElement('ul');DATA.limits.forEach(x=>{const li=document.createElement('li');li.textContent=x;ul.appendChild(li)});$('limits').appendChild(ul);
$('briefdownload').addEventListener('click',()=>download('risk_brief_UNAPPROVED.md',DATA.review.draft,'text/markdown'));
$('evidencedownload').addEventListener('click',()=>download('risk_evidence_UNAPPROVED.json',JSON.stringify({status:'UNAPPROVED_DRAFT',source:DATA.source,inputs:DATA.inputs,evidence:DATA.review.evidence},null,2),'application/json'));
$('exportcsv').addEventListener('click',()=>{const rows=['Date,VaR Forecast,Actual Loss,Breach'];b.dates.forEach((x,i)=>rows.push(`${x},${b.forecast[i]},${b.actual[i]},${b.breaches[i]}`));download('var_backtest.csv',rows.join('\n')+'\n','text/csv')});
document.querySelectorAll('.tab').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('.tab').forEach(x=>{x.classList.toggle('active',x===button);x.setAttribute('aria-selected',x===button?'true':'false');x.tabIndex=x===button?0:-1});document.querySelectorAll('.panel').forEach(x=>x.classList.toggle('active',x.id===button.dataset.target));window.dispatchEvent(new Event('resize'));setTimeout(()=>{document.querySelectorAll('#'+button.dataset.target+' .js-plotly-plot').forEach(x=>Plotly.Plots.resize(x))},50)}));
})();
