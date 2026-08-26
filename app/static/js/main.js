/* ════════════════════════════════════════════════════
   STORAGE
════════════════════════════════════════════════════ */
const LS={
  get:(k,d)=>{try{const v=localStorage.getItem(k);return v!=null?JSON.parse(v):d;}catch{return d;}},
  set:(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v));}catch{}},
  del:(k)=>{try{localStorage.removeItem(k);}catch{}}
};

/* ════ TOAST ════ */
function toast(msg,dur=3200){
  const el=document.getElementById('toast');
  el.textContent=msg;el.classList.add('show');
  clearTimeout(el._t);el._t=setTimeout(()=>el.classList.remove('show'),dur);
}

/* ════ PAGE ROUTING ════ */
function showPage(id){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  const p=document.getElementById(id);
  if(p)p.classList.add('active');
  window.scrollTo(0,0);
}

function showTab(id){
  document.querySelectorAll('.tab-content').forEach(t=>t.style.display='none');
  document.querySelectorAll('.slink').forEach(s=>s.classList.remove('active'));
  const tab=document.getElementById(id);
  if(tab)tab.style.display='block';
  const map={'tab-home':'slink-home','tab-session':'slink-session','tab-history':'slink-history','tab-feedback':'slink-feedback','tab-payment':'slink-payment','tab-settings':'slink-settings'};
  const sl=document.getElementById(map[id]);
  if(sl)sl.classList.add('active');
  window.scrollTo(0,0);
  if(id==='tab-history')renderHistory();
  if(id==='tab-feedback') {
    history.pushState(null, '', '/feedback');
    renderFeedbackTab();
  } else {
    if (window.location.pathname === '/feedback') {
      history.pushState(null, '', '/');
    }
  }
  if(id==='tab-settings')loadSettings();
  if(id==='tab-session'){
    setupState.step=0;
    document.getElementById('session-setup').style.display='block';
    document.getElementById('session-active').style.display='none';
    document.getElementById('session-results').style.display='none';
    refreshSetupStep();
  }
}


/* ════════════════════════════════════════════════════
   AUTH
════════════════════════════════════════════════════ */
const AUTH=(function(){
  const CK='otm_user';
  const TK='otm_token';
  const FREE_DAYS=15,FREE_Q_PER_SESSION=5;

  function getUser(){return LS.get(CK,null);}
  function getToken(){return LS.get(TK,null);}

  async function register(){
    const name=val('su-name').trim();
    const age=val('su-age').trim();
    const gender=val('su-gender');
    const college=val('su-college').trim();
    const email=val('su-email').trim();
    const pass=val('su-pass');
    const pass2=val('su-pass2');
    const err=document.getElementById('signup-err');

    if(!name){return showErr(err,'Please enter your full name.');}
    if(!age||isNaN(age)||age<15||age>70){return showErr(err,'Please enter a valid age (15–70).');}
    if(!gender){return showErr(err,'Please select your gender.');}
    if(!college){return showErr(err,'Please enter your college name.');}
    if(!email||(!email.includes('@')&&email.length<10)){return showErr(err,'Please enter a valid email or phone number.');}
    if(!pass||pass.length<6){return showErr(err,'Password must be at least 6 characters.');}
    if(pass!==pass2){return showErr(err,'Passwords do not match.');}

    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, age, gender, college, email, password: pass})
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Registration failed');
      
      LS.set(TK, data.access_token);
      data.user.trialStart = Date.now();
      LS.set(CK, data.user);
      err.style.display='none';
      loginUser(data.user);
    } catch(e) {
      showErr(err, e.message);
    }
  }

  async function login(){
    const email=val('si-name').trim().toLowerCase();
    const pass=val('si-pass');
    const err=document.getElementById('signin-err');
    if(!email){return showErr(err,'Please enter your email.');}
    if(!pass){return showErr(err,'Please enter your password.');}
    
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password: pass})
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Login failed');
      
      LS.set(TK, data.access_token);
      data.user.trialStart = Date.now();
      LS.set(CK, data.user);
      err.style.display='none';
      loginUser(data.user);
    } catch(e) {
      showErr(err, e.message);
    }
  }

  function demo(){
    const demoUser={uid:'demo@ownthemic.app',name:'Demo User',age:22,gender:'prefer_not',college:'IIT Demo',email:'demo@ownthemic.app',joined:Date.now(),sessions:3,bestScore:74,isPro:false,trialStart:Date.now()};
    LS.set(CK,demoUser);
    loginUser(demoUser);toast('Signed in as Demo User 👋');
  }

  function loginUser(user){
    updateNav(user);
    showPage('pg-dashboard');
    const redirectPath = sessionStorage.getItem('otm_redirect_path') || window.location.pathname;
    sessionStorage.removeItem('otm_redirect_path');
    if (redirectPath === '/feedback') {
      showTab('tab-feedback');
      history.pushState(null, '', '/feedback');
    } else {
      showTab('tab-home');
      history.pushState(null, '', '/');
    }
    updateHomeStats();
    buildFaq();
  }


  function logout(){LS.del(CK);LS.del(TK);showPage('pg-signin');}

  function updateNav(u){
    if(!u)u=getUser();if(!u)return;
    const pill=document.getElementById('user-pill');
    if(pill) {
      if(u.profilePic) {
        pill.innerHTML = `<img src="${u.profilePic}" style="width:20px;height:20px;border-radius:50%;object-fit:cover" /> <span>${u.name.split(' ')[0]}</span>`;
      } else {
        pill.textContent=u.name.split(' ')[0];
      }
    }
    const badge=document.getElementById('plan-badge');
    const trialDays=daysLeft(u);
    if(badge)badge.textContent=u.isPro?'PRO':'FREE TRIAL';
    const td=document.getElementById('trial-days-left');if(td)td.textContent=Math.max(0,trialDays);
    const sd=document.getElementById('stat-days');if(sd)sd.textContent=Math.max(0,trialDays);
  }

  function daysLeft(u){
    const diff=Date.now()-(u.trialStart||Date.now());
    const days=Math.floor(diff/(1000*60*60*24));
    return Math.max(0,FREE_DAYS-days);
  }

  function updateHomeStats(){
    const u=getUser();if(!u)return;
    const sessions=LS.get('otm_sessions',[]).filter(s=>s.uid===u.uid);
    const el1=document.getElementById('stat-sessions');if(el1)el1.textContent=sessions.length;
    const el2=document.getElementById('stat-score');
    if(el2){const scores=sessions.map(s=>s.score).filter(Boolean);el2.textContent=scores.length?Math.max(...scores)+'':' —';}
  }

  function getQuestionsLeft(){const u=getUser();if(!u)return 0;if(u.isPro)return 999;return sessionQLeft;}

  function showErr(el,msg){el.textContent=msg;el.style.display='block';}

  return{register,login,logout,demo,updateNav,getUser,getToken,getQuestionsLeft,updateHomeStats,loginUser};
})();

function val(id){const el=document.getElementById(id);return el?el.value:'';}

/* ════════════════════════════════════════════════════
   SETUP WIZARD
════════════════════════════════════════════════════ */
const setupState={step:0,role:'',qtype:'',difficulty:'Beginner',numQ:3,timer:'on',resume:''};
const SETUP_TITLES=['Choose your role','Select question type','Select difficulty','Session preferences','Add your resume'];
const SETUP_STEPS=5;

function refreshSetupStep(){
  const n=setupState.step;
  for(let i=1;i<=5;i++){const s=document.getElementById('ss'+i);if(s){s.classList.toggle('active',i-1===n);s.style.display=i-1===n?'flex':'none';}}
  const title=document.getElementById('setup-step-title');if(title)title.textContent=`Step ${n+1} of ${SETUP_STEPS} — ${SETUP_TITLES[n]}`;
  const count=document.getElementById('setup-step-count');if(count)count.textContent=`${n+1} / ${SETUP_STEPS}`;
  const prog=document.getElementById('setup-prog');if(prog)prog.style.width=((n+1)/SETUP_STEPS*100)+'%';
  for(let i=0;i<5;i++){const d=document.getElementById('sd'+i);if(d){d.classList.toggle('act',i===n);d.classList.toggle('done',i<n);d.classList.remove('act');d.classList.remove('done');if(i===n)d.classList.add('act');else if(i<n)d.classList.add('done');}}
  const back=document.getElementById('back-btn');if(back)back.style.display=n>0?'inline-flex':'none';
  const skipResume=document.getElementById('skip-resume-btn');if(skipResume)skipResume.style.display=n===4?'block':'none';
  validateSetup();
  if(n===5)checkApiStatus();
}

function validateSetup(){
  const btn=document.getElementById('next-btn');if(!btn)return;
  let ok=false;
  if(setupState.step===0)ok=!!setupState.role;
  else if(setupState.step===1)ok=!!setupState.qtype;
  else if(setupState.step===2)ok=!!setupState.difficulty;
  else if(setupState.step===3)ok=true;
  else if(setupState.step===4)ok=true;
  btn.disabled=!ok;
  if(setupState.step===4){btn.textContent='Start session →';btn.onclick=startSession;}
  else{btn.textContent='Next →';btn.onclick=setupNext;}
}

function setupNext(){if(setupState.step<4){setupState.step++;refreshSetupStep();}else startSession();}
function setupBack(){if(setupState.step>0){setupState.step--;refreshSetupStep();}}

function selectRole(el){document.querySelectorAll('.role-card').forEach(c=>c.classList.remove('sel'));el.classList.add('sel');setupState.role=el.dataset.v;document.getElementById('custom-role').value='';validateSetup();}
function setCustomRole(v){if(v.trim()){document.querySelectorAll('.role-card').forEach(c=>c.classList.remove('sel'));setupState.role=v.trim();}else if(!setupState.role)setupState.role='';validateSetup();}
function selectQtype(el){document.querySelectorAll('.qtype-row').forEach(r=>r.classList.remove('sel'));el.classList.add('sel');setupState.qtype=el.dataset.v;validateSetup();}
function selectDifficulty(el){document.querySelectorAll('#ss3 .setting-row .setting-card').forEach(c=>c.classList.remove('sel'));el.classList.add('sel');setupState.difficulty=el.dataset.v;validateSetup();}
function selectLen(el){document.querySelectorAll('#ss4 .setting-row:first-child .setting-card').forEach(c=>c.classList.remove('sel'));el.classList.add('sel');setupState.numQ=parseInt(el.dataset.v);}
function selectTimer(el){document.querySelectorAll('#ss4 .setting-row:last-child .setting-card').forEach(c=>c.classList.remove('sel'));el.classList.add('sel');setupState.timer=el.dataset.v;}

async function handleResumeFile(input){
  const file=input.files[0];if(!file)return;
  const nm=document.getElementById('rz-file-name');if(nm){nm.textContent='📎 '+file.name;nm.style.display='block';}
  const rm=document.getElementById('rz-remove-btn');if(rm)rm.style.display='block';
  
  const reader=new FileReader();
  reader.onload=e=>{document.getElementById('resume-paste').value=e.target.result||'';setupState.resume=e.target.result||'';};
  reader.readAsText(file);

  // Upload to backend
  const formData = new FormData();
  formData.append('resume', file);
  try {
    const token = AUTH.getToken();
    const headers = {};
    if(token) headers['Authorization'] = 'Bearer ' + token;
    
    const res = await fetch('/api/resume/upload', {
      method: 'POST',
      headers,
      body: formData
    });
    if(!res.ok) throw new Error('Upload failed');
    toast('Resume uploaded successfully!');
  } catch (e) {
    toast('Error uploading resume: ' + e.message);
  }
}
function removeResume(){
  setupState.resume='';
  const input=document.getElementById('rz-input');if(input)input.value='';
  const nm=document.getElementById('rz-file-name');if(nm){nm.textContent='';nm.style.display='none';}
  const rm=document.getElementById('rz-remove-btn');if(rm)rm.style.display='none';
  const ta=document.getElementById('resume-paste');if(ta)ta.value='';
}

function showApiSettings(){setupState.step=5;refreshSetupStep();}

/* ════ PROVIDER / API ════ */
let currentProvider='gemini';

function switchProvider(p,btn){
  currentProvider=p;
  document.querySelectorAll('.prov-panel').forEach(el=>el.style.display='none');
  document.querySelectorAll('#setup-form .ptab').forEach(b=>{b.classList.remove('act');});
  const prov=document.getElementById('prov-'+p);if(prov)prov.style.display='block';
  if(btn)btn.classList.add('act');
  validateSetup();
}

function settingsTab(p,btn){
  currentProvider=p;
  document.querySelectorAll('.set-prov').forEach(el=>el.style.display='none');
  document.querySelectorAll('#settings-ptabs .ptab').forEach(b=>b.classList.remove('act'));
  const prov=document.getElementById('set-prov-'+p);if(prov)prov.style.display='block';
  if(btn)btn.classList.add('act');
  // Pre-fill saved key
  const saved=LS.get('otm_apikey_'+p,'');
  const el=document.getElementById('set-key-'+p);if(el&&saved)el.value=saved;
}

function getActiveKey(){
  const provider = LS.get('otm_provider', 'gemini');
  const key = LS.get('otm_apikey_' + provider, '');
  return {provider, key};
}
function hasKey(){return!!getActiveKey().key;}

// Test key by listing available models
async function listModels(key){
  const r=await fetch('https://generativelanguage.googleapis.com/v1beta/models?key='+key);
  const d=await r.json();
  return d;
}

function checkApiStatus(){
  const {provider,key}=getActiveKey();
  const cm=document.getElementById('api-connected-msg');
  const mm=document.getElementById('api-missing-msg');
  const pn=document.getElementById('api-provider-name');
  if(key){
    if(cm)cm.style.display='block';
    if(mm)mm.style.display='none';
    if(pn)pn.textContent={gemini:'Gemini',groq:'Groq',openrouter:'OpenRouter'}[provider]||provider;
  }else{
    if(cm)cm.style.display='none';
    if(mm)mm.style.display='block';
  }
  validateSetup();
}

function saveApiKey(){
  const key=(document.getElementById('key-'+currentProvider)||{}).value?.trim();
  if(!key){toast('Please enter an API key first.');return;}
  LS.set('otm_apikey_'+currentProvider,key);
  LS.set('otm_provider',currentProvider);
  checkApiStatus();
  toast('✓ API key saved!');
}

async function testApiKey(){
  const key=(document.getElementById('key-'+currentProvider)||{}).value?.trim();
  if(!key){toast('Enter a key first.');return;}
  const res=document.getElementById('api-test-result');
  if(res){res.textContent='Testing…';res.style.display='block';res.className='test-result';}
  try{
    await AI.call('Respond with one word: OK',currentProvider,key);
    if(res){res.textContent='✓ Connection successful!';res.className='test-result ok';}
  }catch(e){
    if(res){res.textContent='❌ '+e.message;res.className='test-result err';}
  }
}

async function testKey(p){
  const key=(document.getElementById('set-key-'+p)||{}).value?.trim()||LS.get('otm_apikey_'+p,'');
  if(!key){toast('Enter or load your key first.');return;}
  const res=document.getElementById('set-test-result');
  if(res){res.textContent='Testing…';res.style.display='block';res.className='test-result';}
  try{
    await AI.call('Respond with one word: OK',p,key);
    if(res){res.textContent='✓ '+p+' key works!';res.className='test-result ok';}
  }catch(e){
    if(res){res.textContent='❌ '+e.message;res.className='test-result err';}
  }
}

function saveKey(p){
  const key=(document.getElementById('set-key-'+p)||{}).value?.trim();
  if(!key){toast('Enter a key first.');return;}
  LS.set('otm_apikey_'+p,key);
  LS.set('otm_provider',p);
  toast('✓ '+p+' API key saved!');
}

/* ════════════════════════════════════════════════════
   AI ENGINE
════════════════════════════════════════════════════ */
const AI=(function(){
  async function callApi(endpoint, data) {
    const keyInfo = getActiveKey();
    const token = AUTH.getToken();
    const headers = {'Content-Type': 'application/json'};
    if(token) headers['Authorization'] = 'Bearer ' + token;
    
    const payload = {...data, provider: keyInfo.provider, key: keyInfo.key};
    
    const res = await fetch(endpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });
    const d = await res.json();
    if(!res.ok) throw new Error(d.error || 'API Error');
    return d;
  }

  async function generateQuestion(role, qtype, difficulty, prevQs=[], resumeText=''){
    const d = await callApi('/api/ai/question', {role, qtype, difficulty, prevQs, resumeText});
    return d.question;
  }

  async function shouldFollowUp(question, answer){
    const d = await callApi('/api/ai/followup', {question, answer});
    return !!d.followup;
  }

  async function generateFollowUp(question, answer, role){
    const d = await callApi('/api/ai/followup', {question, answer, role});
    return d.followup;
  }

  async function scoreSession(role, qtype, qas){
    return await callApi('/api/ai/score', {role, qtype, qas});
  }

  return{generateQuestion, shouldFollowUp, generateFollowUp, scoreSession};
})();

/* ════════════════════════════════════════════════════
   SESSION ENGINE
════════════════════════════════════════════════════ */
const FILLER_WORDS=['um','uh','like','basically','you know','sort of','kind of','literally','actually','right','i mean'];
const DIM_COLORS={contentRelevance:'#7C6FFF',answerStructure:'#7C6FFF',voiceClarity:'#00D4A0',voiceModulation:'#F5A623',fillerControl:'#FF6B4A',answerDepth:'#7C6FFF'};
const DIM_LABELS={contentRelevance:'Content Relevance',answerStructure:'Answer Structure',voiceClarity:'Voice Clarity',voiceModulation:'Voice Modulation',fillerControl:'Filler Word Control',answerDepth:'Answer Depth'};

let sess={questions:[],answers:[],qIndex:0,currentQ:'',currentAnswer:'',recording:false,recognition:null,timerInterval:null,timerSecs:120,wpmStart:0,wordCount:0,wpmWords:0,fillerCount:0,wpmInterval:null,waveAnim:false};
let sessionQLeft=5;
const FREE_SESSION_Q=5;

function showSetup(){document.getElementById('session-setup').style.display='block';document.getElementById('session-active').style.display='none';document.getElementById('session-results').style.display='none';}
function showActive(){document.getElementById('session-setup').style.display='none';document.getElementById('session-active').style.display='block';document.getElementById('session-results').style.display='none';}
function showResults(){document.getElementById('session-setup').style.display='none';document.getElementById('session-active').style.display='none';document.getElementById('session-results').style.display='block';}

async function startSession(){
  const user=AUTH.getUser();if(!user)return;
  // API key optional — falls back to local scoring if absent
  setupState.resume=document.getElementById('resume-paste')?.value||setupState.resume||'';
  showTab('tab-session');showActive();
  // Reset session
  sess={...sess,questions:[],answers:[],qIndex:0,currentQ:'',currentAnswer:'',recording:false};
  sessionQLeft=user.isPro?999:FREE_SESSION_Q;
  // Context chips
  set('ctx-role',setupState.role);set('ctx-qtype',setupState.qtype);set('ctx-timer',setupState.timer==='on'?'2 min timer':'No timer');
  // Free banner
  const fb=document.getElementById('free-banner');if(fb)fb.style.display=user.isPro?'none':'flex';
  set('free-q-left',sessionQLeft);
  // Build waveform bars
  const wb=document.getElementById('wavebox');if(wb&&wb.children.length===0){for(let i=0;i<30;i++){const b=document.createElement('div');b.className='wb';wb.appendChild(b);}}
  await nextQuestion();
}

async function nextQuestion(){
  if(sess.qIndex>=setupState.numQ){await finishSession();return;}
  const user=AUTH.getUser();
  if(!user.isPro&&sessionQLeft<=0){showLocked();return;}
  updateQCount();
  showThinking('Crafting your question…');
  hide('q-bubble');hide('live-panel');hide('mic-area');hide('action-row');hide('locked-msg');hide('tip-bar');

  try{
    const q=await AI.generateQuestion(setupState.role,setupState.qtype,setupState.difficulty,sess.questions,setupState.resume);
    sess.currentQ=q;sess.questions.push(q);
    hideThinking();
    showQuestion(q,false);
    sessionQLeft--;set('free-q-left',Math.max(0,sessionQLeft));
  }catch(e){
    hideThinking();showApiErr(e.message);
  }
}

function updateQCount(){set('q-count-display',`Q ${sess.qIndex+1} of ${setupState.numQ}`);}

function showThinking(msg){
  const el=document.getElementById('thinking-el');
  if(el){
    el.innerHTML=`<div class="t-dots"><div class="td"></div><div class="td"></div><div class="td"></div></div><div class="think-txt" id="think-txt"></div>`;
    el.style.display='flex';
  }
  set('think-txt',msg);
}
function hideThinking(){const el=document.getElementById('thinking-el');if(el)el.style.display='none';}
function showApiErr(msg){
  showThinking('');
  const el=document.getElementById('thinking-el');
  if(el)el.innerHTML=`<div style="color:var(--coral);font-size:.83rem;line-height:1.5">❌ AI Error: ${msg}<br><button onclick="showTab('tab-settings')" style="margin-top:8px;background:var(--purple);color:#fff;border:none;padding:6px 14px;border-radius:100px;cursor:pointer;font-size:.78rem">Try again</button></div>`;
  if(el)el.style.display='flex';
}

function showQuestion(q,isFollowup){
  if (typeof stopSpeech === 'function') stopSpeech();
  show('q-bubble');show('live-panel');show('mic-area');show('action-row');
  set('q-text',q);
  const fu=document.getElementById('followup-tag');if(fu)fu.style.display=isFollowup?'block':'none';
  sess.currentAnswer='';
  const tr=document.getElementById('transcript');if(tr)tr.innerHTML='<span class="ph">Click the mic and speak — your words appear here in real time…</span>';
  set('lv-words','0');set('lv-wpm','—');set('lv-fillers','0');
  const fchips=document.getElementById('lv-fchips');if(fchips)fchips.innerHTML='';
  const sb=document.getElementById('submit-btn');if(sb)sb.disabled=true;
  resetMicUI();
  if(setupState.timer==='on')startTimer();
  // Show tip
  const tips=['Use the STAR method: Situation → Task → Action → Result','Speak at 110–150 words per minute for ideal clarity','Avoid fillers like "um", "basically", and "like"','Give a specific example with a measurable outcome','Start strong — state your main point in the first sentence'];
  const tb=document.getElementById('tip-bar');if(tb){tb.textContent='💡 Tip: '+tips[sess.qIndex%tips.length];tb.style.display='block';}
}

function showLocked(){
  hideThinking();
  const el=document.getElementById('locked-msg');if(el)el.style.display='flex';
  hide('q-bubble');hide('live-panel');hide('mic-area');hide('action-row');
}

/* ── RECORDING ── */
let fillerCounts={};

function toggleRec(){if(sess.recording)stopRec();else startRec();}

function startRec(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)){toast('Speech recognition requires Chrome browser.',4000);return;}
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  sess.recognition=new SR();sess.recognition.continuous=true;sess.recognition.interimResults=true;sess.recognition.lang='en-US';
  fillerCounts={};sess.wordCount=0;sess.wpmWords=0;sess.fillerCount=0;sess.wpmStart=Date.now();
  let finalTrans='';

  sess.recognition.onresult=(ev)=>{
    let interim='';
    for(let i=ev.resultIndex;i<ev.results.length;i++){
      const t=ev.results[i][0].transcript;
      if(ev.results[i].isFinal){finalTrans+=t+' ';processWords(t);}
      else interim+=t;
    }
    const tr=document.getElementById('transcript');
    if(tr){const full=finalTrans+interim;tr.innerHTML=highlightFillers(full)||'<span style="color:var(--text3)">Speaking…</span>';}
    sess.currentAnswer=finalTrans.trim();
    const sb=document.getElementById('submit-btn');if(sb)sb.disabled=sess.currentAnswer.split(/\s+/).filter(w=>w).length<3;
    // Quality bar
    const words=sess.currentAnswer.split(/\s+/).filter(w=>w).length;
    const pct=Math.min(100,words*4);
    const qf=document.getElementById('ql-fill');const qt=document.getElementById('ql-txt');
    if(qf)qf.style.width=pct+'%';
    if(qf){qf.style.backgroundPosition=pct>70?'left':pct>40?'center':'right';}
    if(qt){qt.textContent=pct>70?'Strong':'40'<pct?'Building…':'Keep speaking…';qt.style.color=pct>70?'var(--teal)':pct>40?'var(--amber)':'var(--text3)';}
  };

  sess.recognition.onerror=(e)=>{if(e.error!=='no-speech')toast('Mic: '+e.error,3000);};
  sess.recognition.start();sess.recording=true;
  setRecUI(true);startWave();
  sess.wpmInterval=setInterval(()=>{
    const mins=(Date.now()-sess.wpmStart)/60000;
    if(mins>.05){const wpm=Math.round(sess.wpmWords/mins);const el=document.getElementById('lv-wpm');if(el){el.textContent=wpm;el.className='ls-val'+(wpm<80||wpm>180?' warn':' good');}}
  },1000);
}

function processWords(text){
  const words=text.toLowerCase().split(/\s+/).filter(w=>w);
  sess.wordCount+=words.length;sess.wpmWords+=words.length;set('lv-words',sess.wordCount);
  FILLER_WORDS.forEach(fw=>{
    const re=new RegExp('\\b'+fw+'\\b','gi');const m=text.match(re);
    if(m){fillerCounts[fw]=(fillerCounts[fw]||0)+m.length;sess.fillerCount+=m.length;
      const chips=document.getElementById('lv-fchips');
      if(chips){let chip=chips.querySelector('[data-fw="'+fw+'"]');
        if(chip){chip.textContent='"'+fw+'" ×'+fillerCounts[fw];}
        else{chip=document.createElement('div');chip.className='fchip';chip.dataset.fw=fw;chip.textContent='"'+fw+'" ×'+fillerCounts[fw];chips.appendChild(chip);}
      }
    }
  });
  set('lv-fillers',sess.fillerCount);
  const fe=document.getElementById('lv-fillers');if(fe)fe.className='ls-val'+(sess.fillerCount>6?' bad':sess.fillerCount>3?' warn':' good');
}

function highlightFillers(text){
  FILLER_WORDS.forEach(fw=>{text=text.replace(new RegExp('\\b('+fw+')\\b','gi'),'<mark>$1</mark>');});
  return text;
}

function stopRec(){
  if(sess.recognition){try{sess.recognition.stop();}catch(e){}}
  sess.recognition=null;sess.recording=false;setRecUI(false);stopWave();clearInterval(sess.wpmInterval);
}

function setRecUI(rec){
  const mb=document.getElementById('mic-btn'),rl=document.getElementById('rec-label'),rh=document.getElementById('rec-hint'),tr=document.getElementById('trec'),te=document.getElementById('timer-el');
  if(mb)mb.classList.toggle('rec',rec);
  if(rl){rl.textContent=rec?'Recording…':'Ready to record';rl.classList.toggle('act',rec);}
  if(rh)rh.textContent=rec?'Speak clearly — click submit when done':'Click mic to start speaking';
  if(tr)tr.classList.toggle('show',rec);
  if(te&&setupState.timer==='on')te.style.display=rec?'flex':'none';
}

function resetMicUI(){setRecUI(false);stopWave();clearInterval(sess.wpmInterval);}

function startWave(){
  sess.waveAnim=true;
  const bars=document.querySelectorAll('.wb');
  (function anim(){
    if(!sess.waveAnim)return;
    bars.forEach(b=>{const h=sess.recording?Math.random()*32+3:3;b.style.height=h+'px';b.classList.toggle('act',sess.recording);});
    setTimeout(anim,80);
  })();
}
function stopWave(){sess.waveAnim=false;document.querySelectorAll('.wb').forEach(b=>{b.style.height='3px';b.classList.remove('act');});}

function startTimer(){
  sess.timerSecs=120;clearInterval(sess.timerInterval);
  const te=document.getElementById('timer-el'),tt=document.getElementById('timer-txt');
  if(te)te.style.display='none';
  sess.timerInterval=setInterval(()=>{
    sess.timerSecs--;if(te)te.style.display='flex';
    const m=Math.floor(sess.timerSecs/60),s=String(sess.timerSecs%60).padStart(2,'0');
    if(tt)tt.textContent=m+':'+s;
    if(te)te.className='timer'+(sess.timerSecs<=30?' warn':'')+(sess.timerSecs<=10?' urg':'');
    if(sess.timerSecs<=0){clearInterval(sess.timerInterval);stopRec();submitAnswer();}
  },1000);
}

async function submitAnswer(){
  const answer=sess.currentAnswer.trim();
  stopRec();clearInterval(sess.timerInterval);
  sess.answers.push({question:sess.currentQ,answer,fillerCount:sess.fillerCount,wordCount:sess.wordCount,fillerWords:Object.keys(fillerCounts)});
  sess.qIndex++;
  if(sess.qIndex>=setupState.numQ){await finishSession();return;}
  showThinking('Evaluating your answer…');
  hide('q-bubble');hide('live-panel');hide('mic-area');hide('action-row');
  try{
    if(answer.length>10){
      const fuNeeded=await AI.shouldFollowUp(sess.currentQ,answer);
      if(fuNeeded&&sess.qIndex<setupState.numQ){
        const fuQ=await AI.generateFollowUp(sess.currentQ,answer,setupState.role);
        sess.currentQ=fuQ;sess.questions.push(fuQ);
        sess.qIndex--;hideThinking();showQuestion(fuQ,true);return;
      }
    }
    await nextQuestion();
  }catch(e){await nextQuestion();}
}

function skipQ(){
  sess.answers.push({question:sess.currentQ,answer:'(skipped)',fillerCount:0,wordCount:0,fillerWords:[]});
  sess.qIndex++;stopRec();clearInterval(sess.timerInterval);
  if(sess.qIndex>=setupState.numQ)finishSession();else nextQuestion();
}

function confirmEnd(){if(confirm('End session? Your answers so far will be scored.'))finishSession();}

async function finishSession(){
  if (typeof stopSpeech === 'function') stopSpeech();
  stopRec();clearInterval(sess.timerInterval);
  showActive();
  hide('q-bubble');hide('live-panel');hide('mic-area');hide('action-row');hide('thinking-el');hide('free-banner');hide('tip-bar');
  // Loading state
  const loadEl=document.createElement('div');loadEl.className='loading-wrap';loadEl.id='session-loading';
  loadEl.innerHTML='<div class="spinner"></div><div class="load-txt">Scoring your session with AI…</div><div class="load-sub">Analysing 6 dimensions · Generating model answers</div>';
  document.querySelector('.session-wrap').appendChild(loadEl);

  let result;
  try{result=await AI.scoreSession(setupState.role,setupState.qtype,sess.answers);}
  catch(e){result=localScore();toast('AI scoring unavailable — showing estimate',3000);}
  loadEl.remove();
  renderResults(result);
  saveSession(result);
  showResults();
}

function localScore(){
  const answered=sess.answers.filter(a=>a.answer&&a.answer!=='(skipped)');
  const avg=answered.length?answered.reduce((s,a)=>s+a.wordCount,0)/answered.length:0;
  const tf=sess.answers.reduce((s,a)=>s+a.fillerCount,0);
  const cr=Math.min(92,58+avg/2.5),as=Math.min(88,50+avg/3),vc=72,vm=68,fc=Math.max(28,92-tf*7),ad=Math.min(82,46+avg/4);
  const overall=Math.round(cr*.25+as*.2+vc*.15+vm*.15+fc*.15+ad*.1);
  return{overallScore:overall,scoreLabel:overall>=80?'Excellent':overall>=65?'Good':overall>=50?'Fair':'Needs Work',dimensions:{contentRelevance:{score:Math.round(cr)},answerStructure:{score:Math.round(as)},voiceClarity:{score:vc},voiceModulation:{score:vm},fillerControl:{score:Math.round(fc)},answerDepth:{score:Math.round(ad)}},strengths:'You completed the full session. Good consistency across your answers.',improvements:'Connect your Gemini or Groq API key to get detailed AI-powered feedback.',fillerWords:Object.keys(fillerCounts).slice(0,4),recommendation:'Add a free API key in Settings to unlock full AI scoring and model answers.',questionFeedback:sess.answers.map((_,i)=>({index:i,score:Math.round(50+Math.random()*30),brief:'Connect AI for detailed feedback.',modelAnswer:'Add your free API key to see ideal STAR answers.'}))};
}

function renderResults(res){
  const score=res.overallScore||0;
  // Ring
  const rn=document.getElementById('ring-num');if(rn){rn.textContent=score;rn.style.color=score>=80?'#00D4A0':score>=60?'#7C6FFF':'#F5A623';}
  const arc=document.getElementById('res-arc');
  if(arc)setTimeout(()=>{const c=490.1;arc.style.strokeDashoffset=c*(1-score/100);},100);
  // Sub
  set('res-headline','Confidence Score: '+score+'/100 · '+res.scoreLabel);
  set('res-sub',(sess.answers.filter(a=>a.answer!=='(skipped)').length)+' of '+sess.answers.length+' questions answered · '+setupState.role);

  // Dimension bars
  const db=document.getElementById('dim-bars');if(db){
    db.innerHTML='';
    Object.entries(res.dimensions||{}).forEach(([k,v])=>{
      const col=DIM_COLORS[k]||'#7C6FFF';const lbl=DIM_LABELS[k]||k;const sc=v.score||0;
      const row=document.createElement('div');row.className='drow';
      row.innerHTML=`<div class="dlbl">${lbl}</div><div class="dtrack"><div class="dfill" style="background:${col}" data-w="${sc}%"></div></div><div class="dpct" style="color:${col}">${sc}%</div>`;
      db.appendChild(row);
    });
    setTimeout(()=>db.querySelectorAll('.dfill').forEach(b=>b.style.width=b.dataset.w),150);
  }

  // AI rec
  if(res.recommendation){const ar=document.getElementById('ai-rec');const at=document.getElementById('ai-rec-txt');if(ar)ar.style.display='block';if(at)at.textContent=res.recommendation;}

  // FB cards
  const fg=document.getElementById('fb-grid');
  if(fg)fg.innerHTML=`<div class="fb-card"><div class="fb-tag str">✦ What's working</div><div class="fb-body">${res.strengths||'—'}</div></div><div class="fb-card"><div class="fb-tag imp">▲ Key improvements</div><div class="fb-body">${res.improvements||'—'}${res.fillerWords?.length?'<div class="fword-list">'+res.fillerWords.map(w=>'<span class="fword">'+w+'</span>').join('')+'</div>':''}</div></div>`;

  // QA list
  const ql=document.getElementById('qa-list');if(ql){
    ql.innerHTML='';
    sess.answers.forEach((qa,i)=>{
      const fb=(res.questionFeedback||[]).find(f=>f.index===i)||{};
      const sc=fb.score||0;const cls=sc>=75?'good':sc>=50?'mid':'low';
      const item=document.createElement('div');item.className='qa-item';
      item.innerHTML=`<div class="qa-header" onclick="this.nextElementSibling.classList.toggle('open');this.querySelector('.qa-tog').classList.toggle('open')"><div class="qa-q-wrap"><div class="qa-q"><b>Q${i+1}</b>${qa.question}</div><div class="qa-a">${qa.answer||'(skipped)'}</div>${fb.score!=null?'<span class="qa-score '+cls+'">'+sc+'/100</span>':''}${fb.brief?'<div style="font-size:.72rem;color:var(--text3);margin-top:3px;font-style:italic">'+fb.brief+'</div>':''}</div><div class="qa-tog">▾</div></div><div class="model-block">${fb.modelAnswer?'<div class="model-lbl">Model Answer</div><div class="model-txt">'+fb.modelAnswer+'</div>':'<div style="font-size:.78rem;color:var(--text3);padding:10px 0">Connect AI for model answers.</div>'}</div>`;
      ql.appendChild(item);
    });
  }

  // Upgrade row for free users
  const user=AUTH.getUser();
  const ur=document.getElementById('upgrade-row');if(ur)ur.style.display=user?.isPro?'none':'flex';
}

async function saveSession(res){
  const payload = {
    role: setupState.role,
    qtype: setupState.qtype,
    overallScore: res.overallScore,
    scoreLabel: res.scoreLabel,
    strengths: res.strengths,
    improvements: res.improvements,
    recommendation: res.recommendation,
    dimensions: res.dimensions,
    aiProvider: res.aiProvider || currentProvider,
    qas: sess.answers.map(a => ({
      question: a.question,
      answer: a.answer,
      fillerCount: a.fillerCount,
      wordCount: a.wordCount
    })),
    questionFeedback: res.questionFeedback
  };
  
  try {
    const token = AUTH.getToken();
    const headers = {'Content-Type': 'application/json'};
    if(token) headers['Authorization'] = 'Bearer ' + token;
    
    await fetch('/api/session/save', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });
    AUTH.updateHomeStats();
  } catch(e) {
    console.error('Failed to save session to backend', e);
  }
}

function startNewSession(){showSetup();setupState.step=0;refreshSetupStep();}
function copyScore(){
  const sc=document.getElementById('ring-num')?.textContent||'?';
  navigator.clipboard.writeText(`I scored ${sc}/100 on OwnTheMic AI Interview Coach!\nRole: ${setupState.role} | ${setupState.qtype}\nPractice free at OwnTheMic`).then(()=>toast('Score copied!'));
}

/* Session feedback */
let sessionRating=0;
function rateStar(n){sessionRating=n;document.querySelectorAll('.rfb-star').forEach((s,i)=>s.classList.toggle('lit',i<n));}
function submitSessionFeedback(){
  const comment=document.getElementById('rfb-comment')?.value||'';
  const user=AUTH.getUser();
  const fb={ts:Date.now(),uid:user?.uid,role:setupState.role,qtype:setupState.qtype,rating:sessionRating,comment,score:parseInt(document.getElementById('ring-num')?.textContent||'0')};
  const existing=LS.get('otm_feedback',[]);existing.push(fb);LS.set('otm_feedback',existing);
  const done=document.getElementById('rfb-done');if(done)done.style.display='flex';
  toast('Feedback saved — thank you!');
}

/* ════ HISTORY ════ */
async function renderHistory(){
  const w=document.getElementById('history-list');if(!w)return;
  w.innerHTML='<div class="loading-wrap"><div class="spinner"></div></div>';
  
  try {
    const token = AUTH.getToken();
    const headers = {};
    if(token) headers['Authorization'] = 'Bearer ' + token;
    
    const res = await fetch('/api/session/history', {headers});
    const data = await res.json();
    
    if(!data.sessions || data.sessions.length===0){
      w.innerHTML=`<div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <div class="empty-state-title">No sessions recorded yet</div>
        <div class="empty-state-desc">Start practicing by opening the "Practice" tab and speaking your first answer!</div>
      </div>`;
      return;
    }
    
    let html='';
    data.sessions.forEach(s=>{
      const dt=new Date(s.date).toLocaleDateString('en-IN', {day:'numeric', month:'short', year:'numeric'});
      const sc=s.overallScore||0;
      const cl=sc>=80?'good':sc>=60?'mid':'low';
      html+=`<div class="history-item">
        <div class="hi-score ${cl}">${sc}</div>
        <div class="hi-info">
          <div class="hi-role">${s.role} — ${s.qtype}</div>
          <div class="hi-meta">${dt}</div>
        </div>
        <div class="hi-date">${dt}</div>
      </div>`;
    });
    w.innerHTML=html;
  } catch (e) {
    w.innerHTML='<div style="color:var(--color-danger);padding:20px;text-align:center">Failed to load history</div>';
  }
}

/* ════ SETTINGS ════ */
function loadSettings(){
  const user=AUTH.getUser();if(!user)return;
  ['name','email','college','age'].forEach(f=>{const el=document.getElementById('set-'+f);if(el)el.value=user[f]||'';});
  // Pre-fill saved keys
  ['gemini','groq','openrouter'].forEach(p=>{const k=LS.get('otm_apikey_'+p,'');const el=document.getElementById('set-key-'+p);if(el&&k)el.value=k;});
}

function saveProfile(){
  const user=AUTH.getUser();if(!user)return;
  const users=LS.get('otm_users',{});
  const updates={name:val('set-name').trim()||user.name,email:val('set-email').trim()||user.email,college:val('set-college').trim()||user.college,age:val('set-age')||user.age};
  if(users[user.uid])Object.assign(users[user.uid],updates);
  LS.set('otm_users',users);
  LS.set('otm_user',{...user,...updates});
  AUTH.updateNav();toast('Profile saved ✓');
}

function clearData(){
  if(confirm('Clear all session history from this device? Your account will remain.')){LS.del('otm_sessions');LS.del('otm_feedback');toast('Session data cleared.');}}

function showApiErr(){} // covered by inline

/* ════ PAYMENT ════ */
function initiatePayment(plan){
  const plans={'pro-monthly':'₹99/month','max-annual':'₹999/year'};
  toast(`Razorpay integration coming soon! Plan: ${plans[plan]} · Contact: hello@ownthemic.app`,5000);
  PAYWALL.close();
}

/* ════ PAYWALL ════ */
const PAYWALL=(function(){
  function open(){const m=document.getElementById('paywall-modal');if(m)m.classList.add('open');}
  function close(){const m=document.getElementById('paywall-modal');if(m)m.classList.remove('open');}
  return{open,close};
})();

/* ════ FAQ ════ */
function buildFaq(){
  const faqs=[
    {q:'Is OwnTheMic really free?',a:'Yes! Your 15-day trial gives you full access to everything. After that, the free plan gives you 5 questions per session to practice with. Upgrade to Pro for unlimited sessions.'},
    {q:'What\'s the difference between Gemini and Groq?',a:'Both are free AI providers. Gemini (Google) gives better quality responses — great for scoring and model answers. Groq is ultra-fast (300+ tokens/second) — ideal if you want instant question generation. We recommend Gemini for best results.'},
    {q:'Is my API key safe?',a:'Yes. Your API key is stored only in your browser\'s localStorage. It never gets sent to our servers. All AI calls go directly from your browser to Google or Groq\'s servers.'},
    {q:'Does it work on my phone?',a:'The dashboard and setup work on mobile. However, live voice recording works best on Chrome desktop. The Web Speech API has limited mobile support.'},
    {q:'Can I cancel Pro anytime?',a:'Yes. No lock-in contracts. Cancel from your account settings and you\'ll retain access until the end of your billing period.'},
    {q:'How is the Confidence Score calculated?',a:'It\'s a weighted average of 6 dimensions: Content Relevance (25%), Answer Structure (20%), Voice Clarity (15%), Voice Modulation (15%), Filler Word Control (15%), and Answer Depth (10%). Each is scored 0–100 by the AI.'}
  ];
  const el=document.getElementById('faq-list');if(!el)return;
  el.innerHTML=faqs.map((f,i)=>`<div style="border:1px solid var(--border);border-radius:13px;overflow:hidden;margin-bottom:8px"><div onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='block'?'none':'block'" style="padding:14px 18px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:.85rem;font-weight:600" onmouseover="this.style.background='rgba(255,255,255,.015)'" onmouseout="this.style.background=''">${f.q}<span style="color:var(--text3);font-size:1rem;flex-shrink:0">▾</span></div><div style="display:none;padding:0 18px 14px;font-size:.82rem;color:var(--text2);line-height:1.65;font-weight:300">${f.a}</div></div>`).join('');
}

/* ════ HELPERS ════ */
function set(id,v){const el=document.getElementById(id);if(el)el.textContent=v;}
function show(id){const el=document.getElementById(id);if(el)el.style.display='block';}
function hide(id){const el=document.getElementById(id);if(el)el.style.display='none';}


/* ════ SITE FEEDBACK ════ */
const surveyQuestions = [
  {
    id: 'challenge',
    title: 'What challenge were you hoping OwnTheMic would help you with?',
    type: 'checkbox',
    options: [
      { value: 'Fear of interviews', label: 'Fear of interviews' },
      { value: 'Speaking confidently', label: 'Speaking confidently' },
      { value: 'Answering better', label: 'Answering better' },
      { value: 'Improving communication', label: 'Improving communication' },
      { value: 'other', label: 'Other', hasInput: true }
    ],
    required: true
  },
  {
    id: 'ai_feedback_helpful',
    title: 'Did the AI feedback help you improve your response?',
    type: 'radio',
    options: [
      { value: 'Yes', label: 'Yes' },
      { value: 'Somewhat', label: 'Somewhat' },
      { value: 'No', label: 'No' }
    ],
    required: true
  },
  {
    id: 'most_valuable_feedback',
    title: 'Which part of the feedback was most valuable?',
    type: 'checkbox',
    options: [
      { value: 'Voice & tone', label: 'Voice & tone' },
      { value: 'Content quality', label: 'Content quality' },
      { value: 'Filler words', label: 'Filler words' },
      { value: 'Confidence', label: 'Confidence' },
      { value: 'Overall suggestions', label: 'Overall suggestions' },
      { value: 'other', label: 'Other', hasInput: true }
    ],
    required: true
  },
  {
    id: 'confusing_inaccurate_unnecessary',
    title: 'Was anything confusing, inaccurate, or unnecessary?',
    type: 'textarea',
    placeholder: 'e.g. The scoring explanation wasn\'t clear until I scrolled far down…',
    required: false
  },
  {
    id: 'would_use_again',
    title: 'Would you use OwnTheMic again before your next interview?',
    type: 'radio',
    options: [
      { value: 'Definitely', label: 'Definitely' },
      { value: 'Maybe', label: 'Maybe' },
      { value: 'No', label: 'No' }
    ],
    required: true
  },
  {
    id: 'desired_improvement',
    title: 'What\'s the one feature or improvement that would make OwnTheMic even more valuable to you?',
    type: 'textarea',
    placeholder: 'e.g. The live filler word tracker looks really useful…',
    required: false
  },
  {
    id: 'pro_interest',
    title: 'If OwnTheMic offered a Pro version with advanced interview practice and personalised feedback, would you consider paying for it?',
    type: 'radio',
    options: [
      { value: 'Yes', label: 'Yes' },
      { value: 'Maybe', label: 'Maybe' },
      { value: 'No', label: 'No' }
    ],
    required: true
  }
];

let surveyCurrentStep = 0;
let surveyAnswers = {};
let surveySubmitted = false;

async function checkSurveyStatus() {
  const token = AUTH.getToken();
  if (!token) return;
  try {
    const res = await fetch('/api/feedback/pilot/status', {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    const d = await res.json();
    surveySubmitted = !!d.submitted;
  } catch(e) {
    console.error('Error fetching survey status:', e);
  }
}

async function renderFeedbackTab() {
  const user = AUTH.getUser();
  if (!user) return;

  await checkSurveyStatus();

  const intro = document.getElementById('survey-intro-view');
  const wizard = document.getElementById('survey-wizard-view');
  const success = document.getElementById('survey-success-view');

  if (surveySubmitted) {
    if (intro) intro.style.display = 'none';
    if (wizard) wizard.style.display = 'none';
    if (success) success.style.display = 'block';
  } else {
    if (intro) intro.style.display = 'block';
    if (wizard) wizard.style.display = 'none';
    if (success) success.style.display = 'none';
  }
}

function startSurvey() {
  surveyCurrentStep = 0;
  surveyAnswers = {};
  showSurveyStep();
}

function showSurveyStep() {
  const intro = document.getElementById('survey-intro-view');
  const wizard = document.getElementById('survey-wizard-view');
  const success = document.getElementById('survey-success-view');

  if (intro) intro.style.display = 'none';
  if (success) success.style.display = 'none';
  if (wizard) wizard.style.display = 'block';

  const q = surveyQuestions[surveyCurrentStep];
  const stepsCount = surveyQuestions.length;

  // Update headers & progress bar
  const stepTitle = document.getElementById('survey-step-title');
  if (stepTitle) stepTitle.textContent = `Question ${surveyCurrentStep + 1} of ${stepsCount}`;
  
  const stepPct = document.getElementById('survey-step-pct');
  const pct = Math.round(((surveyCurrentStep + 1) / stepsCount) * 100);
  if (stepPct) stepPct.textContent = `${pct}% completed`;

  const progBar = document.getElementById('survey-progress-bar');
  if (progBar) progBar.style.width = `${pct}%`;

  const prevBtn = document.getElementById('survey-prev-btn');
  if (prevBtn) prevBtn.style.display = surveyCurrentStep > 0 ? 'inline-flex' : 'none';

  const nextBtn = document.getElementById('survey-next-btn');
  if (nextBtn) {
    if (surveyCurrentStep === stepsCount - 1) {
      nextBtn.textContent = 'Submit Feedback';
    } else {
      nextBtn.textContent = 'Next →';
    }
  }

  // Render active question HTML
  const area = document.getElementById('survey-question-area');
  if (!area) return;

  area.innerHTML = buildQuestionHTML(q);
  validateSurveyStep();
}

function buildQuestionHTML(q) {
  let html = `<div style="font-family:var(--font); font-size:1.1rem; font-weight:700; letter-spacing:-.02em; margin-bottom:20px; color:var(--text);">${q.title}</div>`;

  if (q.type === 'checkbox' || q.type === 'radio') {
    html += `<div style="display:flex; flex-direction:column; gap:12px;">`;
    q.options.forEach((opt, idx) => {
      const isSelected = isOptionSelected(q.id, opt.value);
      const isOther = opt.hasInput;
      const otherText = isOther ? (surveyAnswers[q.id + '_other'] || '') : '';
      
      html += `
        <div class="survey-option-card ${isSelected ? 'sel' : ''}" 
             onclick="selectSurveyOption('${q.id}', '${opt.value}', ${q.type === 'radio' ? 'true' : 'false'}, ${isOther ? 'true' : 'false'})" 
             style="background:rgba(255,255,255,.03); border:1.5px solid ${isSelected ? 'var(--color-primary)' : 'var(--border2)'}; border-radius:var(--radius-sm); padding:16px 20px; cursor:pointer; transition:all .2s; display:flex; flex-direction:column; gap:10px;">
          <div style="display:flex; align-items:center; gap:12px;">
            <input type="${q.type}" name="${q.id}" value="${opt.value}" ${isSelected ? 'checked' : ''} style="accent-color:var(--purple); width:18px; height:18px; cursor:pointer;" onclick="event.stopPropagation(); selectSurveyOption('${q.id}', '${opt.value}', ${q.type === 'radio' ? 'true' : 'false'}, ${isOther ? 'true' : 'false'})">
            <span style="font-size:0.9rem; color:var(--text2); font-weight:500;">${opt.label}</span>
          </div>
          ${isOther && isSelected ? `
            <div onclick="event.stopPropagation();" style="margin-top:6px;">
              <input type="text" id="${q.id}-other-input" 
                     placeholder="Please specify..." 
                     value="${otherText}" 
                     oninput="updateSurveyOtherInput('${q.id}', this.value)"
                     style="background:rgba(255,255,255,.04); border:1px solid var(--border2); border-radius:var(--radius-xs); padding:8px 12px; color:var(--text); font-size:0.85rem; outline:none; width:100%; box-sizing:border-box;">
            </div>
          ` : ''}
        </div>
      `;
    });
    html += `</div>`;
  } else if (q.type === 'textarea') {
    const val = surveyAnswers[q.id] || '';
    html += `
      <div class="field">
        <textarea id="${q.id}-textarea" 
                  placeholder="${q.placeholder || ''}" 
                  oninput="updateSurveyTextarea('${q.id}', this.value)"
                  style="width:100%; background:rgba(255,255,255,.04); border:1px solid var(--border2); border-radius:var(--radius-sm); padding:14px; color:var(--text); font-family:var(--body); font-size:.88rem; outline:none; resize:vertical; min-height:120px; line-height:1.6; transition:border-color .2s; box-sizing:border-box;">${val}</textarea>
      </div>
    `;
  }

  // Handle Q7 Conditional pricing follow up
  if (q.id === 'pro_interest') {
    const selVal = surveyAnswers[q.id];
    const showPrice = selVal === 'Yes' || selVal === 'Maybe';
    const isPriceYes = surveyAnswers['pro_price_interest'] === 'Yes';
    const isPriceNo = surveyAnswers['pro_price_interest'] === 'No';
    
    html += `
      <div id="pro-price-conditional" style="margin-top:24px; padding-top:20px; border-top:1px dashed rgba(255,255,255,0.1); display:${showPrice ? 'block' : 'none'};">
        <div style="font-family:var(--font); font-size:0.95rem; font-weight:700; margin-bottom:12px; color:var(--text);">If yes, would you consider a fair monthly price of ₹99–129?</div>
        <div style="display:flex; gap:12px;">
          <div class="survey-option-card ${isPriceYes ? 'sel' : ''}" 
               onclick="selectConditionalPrice('Yes')" 
               style="flex:1; text-align:center; padding:12px; border:1.5px solid ${isPriceYes ? 'var(--color-primary)' : 'var(--border2)'}; border-radius:var(--radius-sm); background:rgba(255,255,255,.02); cursor:pointer; font-size:0.85rem; font-weight:600; color:var(--text2);">
            Yes
          </div>
          <div class="survey-option-card ${isPriceNo ? 'sel' : ''}" 
               onclick="selectConditionalPrice('No')" 
               style="flex:1; text-align:center; padding:12px; border:1.5px solid ${isPriceNo ? 'var(--color-primary)' : 'var(--border2)'}; border-radius:var(--radius-sm); background:rgba(255,255,255,.02); cursor:pointer; font-size:0.85rem; font-weight:600; color:var(--text2);">
            No
          </div>
        </div>
      </div>
    `;
  }

  return html;
}

function isOptionSelected(fieldId, value) {
  const current = surveyAnswers[fieldId];
  if (!current) return false;
  if (Array.isArray(current)) {
    return current.includes(value);
  }
  return current === value;
}

function selectSurveyOption(fieldId, value, isSingleSelect, isOther) {
  if (isSingleSelect) {
    surveyAnswers[fieldId] = value;
    if (fieldId === 'pro_interest') {
      if (value !== 'Yes' && value !== 'Maybe') {
        delete surveyAnswers['pro_price_interest'];
      }
    }
  } else {
    if (!surveyAnswers[fieldId]) surveyAnswers[fieldId] = [];
    const idx = surveyAnswers[fieldId].indexOf(value);
    if (idx > -1) {
      surveyAnswers[fieldId].splice(idx, 1);
      if (isOther) {
        delete surveyAnswers[fieldId + '_other'];
      }
    } else {
      surveyAnswers[fieldId].push(value);
    }
  }

  // Rerender active step to update UI state, keeping conditional display check
  showSurveyStep();
}

function updateSurveyOtherInput(fieldId, value) {
  surveyAnswers[fieldId + '_other'] = value;
  validateSurveyStep();
}

function updateSurveyTextarea(fieldId, value) {
  surveyAnswers[fieldId] = value;
  validateSurveyStep();
}

function selectConditionalPrice(value) {
  surveyAnswers['pro_price_interest'] = value;
  showSurveyStep();
}

function validateSurveyStep() {
  const q = surveyQuestions[surveyCurrentStep];
  const nextBtn = document.getElementById('survey-next-btn');
  if (!nextBtn) return;

  let isValid = true;
  if (q.required) {
    const val = surveyAnswers[q.id];
    if (!val || (Array.isArray(val) && val.length === 0)) {
      isValid = false;
    } else {
      // Check other option input
      if (Array.isArray(val) && val.includes('other')) {
        const otherVal = surveyAnswers[q.id + '_other'] || '';
        if (!otherVal.trim()) {
          isValid = false;
        }
      }
      
      // Question 7 Pro interest conditional price validation
      if (q.id === 'pro_interest' && (val === 'Yes' || val === 'Maybe')) {
        const priceInterest = surveyAnswers['pro_price_interest'];
        if (!priceInterest) {
          isValid = false;
        }
      }
    }
  }

  nextBtn.disabled = !isValid;
}

function prevSurveyStep() {
  if (surveyCurrentStep > 0) {
    surveyCurrentStep--;
    showSurveyStep();
  }
}

async function nextSurveyStep() {
  const stepsCount = surveyQuestions.length;
  if (surveyCurrentStep < stepsCount - 1) {
    surveyCurrentStep++;
    showSurveyStep();
  } else {
    await submitSurvey();
  }
}

async function submitSurvey() {
  const token = AUTH.getToken();
  if (!token) return;

  const btn = document.getElementById('survey-next-btn');
  if (btn) btn.disabled = true;

  // Format responses
  const formattedAnswers = {};
  surveyQuestions.forEach(q => {
    const rawVal = surveyAnswers[q.id];
    if (Array.isArray(rawVal)) {
      // Map 'other' to text value if selected
      const mapped = rawVal.map(v => {
        if (v === 'other') {
          return `Other: ${surveyAnswers[q.id + '_other'] || ''}`;
        }
        return v;
      });
      formattedAnswers[q.id] = mapped.join(', ');
    } else {
      formattedAnswers[q.id] = rawVal || '';
    }
  });

  // Question 7 follow-up monthly pricing option
  formattedAnswers['pro_price_interest'] = surveyAnswers['pro_price_interest'] || '';

  try {
    const res = await fetch('/api/feedback/pilot', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      },
      body: JSON.stringify(formattedAnswers)
    });
    
    const d = await res.json();
    if (!res.ok) throw new Error(d.error || 'Submission failed');
    
    surveySubmitted = true;
    toast('Thank you! Feedback saved ✓');
    
    const wizard = document.getElementById('survey-wizard-view');
    const success = document.getElementById('survey-success-view');
    if (wizard) wizard.style.display = 'none';
    if (success) success.style.display = 'block';
  } catch(e) {
    toast('Error: ' + e.message);
    if (btn) btn.disabled = false;
  }
}


/* ════ TTS ════ */
let ttsUtterance = null;
let ttsVoice = null;
let isSpeaking = false;

function initTTS() {
  if (!('speechSynthesis' in window)) {
    const btn = document.getElementById('tts-btn');
    if (btn) {
      btn.style.opacity = '0.3';
      btn.style.cursor = 'not-allowed';
      btn.title = "Voice playback isn't supported on this browser.";
      btn.onclick = null;
    }
    return;
  }
  
  const setVoice = () => {
    const voices = window.speechSynthesis.getVoices();
    if (!voices.length) return;
    let best = voices.find(v => v.lang.startsWith('en') && (v.name.toLowerCase().includes('female') || v.name.toLowerCase().includes('samantha') || v.name.toLowerCase().includes('victoria') || v.name.toLowerCase().includes('zira')));
    if (!best) best = voices.find(v => v.lang.startsWith('en') && v.name.toLowerCase().includes('google'));
    if (!best) best = voices.find(v => v.lang.startsWith('en'));
    if (!best) best = voices[0];
    ttsVoice = best;
  };
  
  setVoice();
  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = setVoice;
  }
}

function stopSpeech() {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  isSpeaking = false;
  updateTTSIcon(false);
}

function toggleSpeech() {
  if (!('speechSynthesis' in window)) return;
  
  if (window.speechSynthesis.speaking) {
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      isSpeaking = true;
      updateTTSIcon(true);
    } else {
      window.speechSynthesis.pause();
      isSpeaking = false;
      updateTTSIcon(false);
    }
    return;
  }

  const text = document.getElementById('q-text')?.textContent;
  if (!text) return;
  
  stopSpeech();
  
  ttsUtterance = new SpeechSynthesisUtterance(text);
  if (ttsVoice) ttsUtterance.voice = ttsVoice;
  ttsUtterance.rate = 0.9;
  ttsUtterance.pitch = 1.0;
  
  ttsUtterance.onstart = () => {
    isSpeaking = true;
    updateTTSIcon(true);
  };
  ttsUtterance.onend = () => {
    isSpeaking = false;
    updateTTSIcon(false);
  };
  ttsUtterance.onerror = () => {
    isSpeaking = false;
    updateTTSIcon(false);
  };
  
  window.speechSynthesis.speak(ttsUtterance);
}

function updateTTSIcon(active) {
  const btn = document.getElementById('tts-btn');
  const normal = document.getElementById('tts-icon-normal');
  const speaking = document.getElementById('tts-icon-speaking');
  if (!btn || !normal || !speaking) return;
  
  if (active) {
    btn.classList.add('speaking');
    normal.style.display = 'none';
    speaking.style.display = 'block';
  } else {
    btn.classList.remove('speaking');
    normal.style.display = 'block';
    speaking.style.display = 'none';
  }
}

/* ════ GOOGLE OAUTH CALLBACK ════ */
window.handleGoogleCredential = async function(response) {
  try {
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ id_token: response.credential })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Google login failed');
    
    LS.set('otm_token', data.access_token);
    data.user.trialStart = Date.now();
    LS.set('otm_user', data.user);
    AUTH.updateNav(data.user);
    AUTH.loginUser(data.user);
    toast('Signed in with Google! 👋');
  } catch (e) {
    toast('Google Login Error: ' + e.message);
  }
};

/* ════ INIT ════ */
window.addEventListener('DOMContentLoaded',()=>{
  initTTS();
  const user=AUTH.getUser();
  const path=window.location.pathname;
  if(user){
    AUTH.updateNav(user);
    showPage('pg-dashboard');
    if(path==='/feedback'){
      showTab('tab-feedback');
    }else{
      showTab('tab-home');
    }
    AUTH.updateHomeStats();
    buildFaq();
  }else{
    if(path==='/feedback'){
      sessionStorage.setItem('otm_redirect_path','/feedback');
    }
    showPage('pg-signup');
  }
  // Wave bars for session
  const wb=document.getElementById('wavebox');
  if(wb){for(let i=0;i<30;i++){const b=document.createElement('div');b.className='wb';wb.appendChild(b);}}
});