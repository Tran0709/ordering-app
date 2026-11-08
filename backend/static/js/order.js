// 菜园子 online ordering – menu, cart, ordering hours, checkout
// [id, 中文, English, MP price, U.P price, section, image slug, extra]
const S = {
  sig:  ["招牌必点","Signature Dishes"],
  garden:["菜园子拿手菜","Garden Signature Dish"],
  cold: ["开胃小碟","Pickled & Cold Appetizers"],
  rice: ["经典下饭菜","Classic Rice Dishes"],
  chef: ["大厨精烹","Chef's Exquisite Cuisine"],
  steam:["蒸蒸日上","Steamed Dishes"],
  soup: ["滋补靓汤","Nourishing Soups"],
  veg:  ["我家菜园子","Home Garden Vegetables"],
  dim:  ["老长沙点心","Changsha Dim Sum"],
  drink:["酒水饮料","Beverages"],
};
let M = []; // filled from /api/menu (backend/menu.json) on load

const $=s=>document.querySelector(s), money=n=>"$"+n.toFixed(2);
let byId={};
let member=false, cart={}, optSel={}; // cart key: id|optIndex -> qty
try{cart=JSON.parse(localStorage.getItem("cyz-cart")||"{}");member=localStorage.getItem("cyz-member")==="1"}catch(e){}
$("#member").checked=member;

function unit(key){const [id,o]=key.split("|"),m=byId[id];if(!m)return 0;const ex=m[7]||{};
  const p=ex.opts?ex.opts[+o]:[null,m[3],m[4]];return member?p[1]:p[2]}
function label(key){const [id,o]=key.split("|"),m=byId[id],ex=m[7]||{};return ex.opts?ex.opts[+o][0]:""}
function save(){try{localStorage.setItem("cyz-cart",JSON.stringify(cart));localStorage.setItem("cyz-member",member?"1":"0")}catch(e){}}

function priceHTML(mp,up){return mp===up
  ?`<div class="price member"><span class="mp">$${fmt(up)}</span></div>`
  :`<div class="price ${member?"member":""}"><div><span class="mp">$${fmt(mp)}</span><small>MP会员价</small></div><div class="up">$${fmt(up)}<small>U.P原价</small></div></div>`}
function fmt(n){return (Math.round(n*100)/100).toString()}
function cardHTML(m){const [id,zh,en,mp,up,,img,ex={}]=m,o=optSel[id]||0,p=ex.opts?ex.opts[o]:[0,mp,up];
  return `<article class="card"><div class="ph"><img loading="lazy" src="/img/${img}.jpg" alt="${en}">${ex.badge?`<span class="badge">${ex.badge}</span>`:""}</div>
  <div class="info"><div class="row"><div><div class="zh">${zh}</div><div class="en">${en}</div></div>${priceHTML(p[1],p[2])}</div>
  ${ex.opts?`<div class="opts">${ex.opts.map((x,i)=>`<button class="${i==o?"on":""}" onclick="pickOpt('${id}',${i})">${x[0]}</button>`).join("")}</div>`:""}
  <div class="add"><span class="note">${ex.note||""}</span>${ctrl(id+"|"+(ex.opts?o:0))}</div></div></article>`}
function ctrl(key){const q=cart[key]||0;return q?`<span class="qty"><button onclick="chg('${key}',-1)" aria-label="Remove one">−</button><b>${q}</b><button onclick="chg('${key}',1)" aria-label="Add one">+</button></span>`
  :`<button class="plus" onclick="chg('${key}',1)">+ Add</button>`}

function render(){
  let h="";for(const k in S){const items=M.filter(m=>m[5]===k);
    h+=`<section class="sec" id="s-${k}"><div class="banner"><h2>${S[k][0]}</h2><em>${S[k][1]}</em></div>`;
    if(k==="drink"){const g={};items.forEach(m=>(g[m[7].group]??=[]).push(m));
      h+=`<div class="drinks">${Object.entries(g).map(([n,l])=>`<div class="dcol"><h3>${n}</h3>${l.map(m=>`<div class="drow"><img loading="lazy" src="/img/${m[6]}.jpg" alt=""><div class="t"><b>${m[1]}</b><span class="en">${m[2]}</span></div><span class="p">$${m[4].toFixed(2)}</span>${ctrl(m[0]+"|0")}</div>`).join("")}</div>`).join("")}</div>`}
    else{const hero=items.filter(m=>m[7]?.hero),rest=items.filter(m=>!m[7]?.hero);
      if(hero.length)h+=`<div class="hero">${hero.map(cardHTML).join("")}${rest.slice(0,1).map(cardHTML).join("")}</div>`,rest.shift();
      h+=`<div class="grid">${rest.map(cardHTML).join("")}</div>`}
    h+=`</section>`}
  $("#menu").innerHTML=h;
  $("#nav").innerHTML=Object.entries(S).map(([k,v])=>`<a href="#s-${k}" data-k="${k}">${v[0]}</a>`).join("");
  totals();
  if(window.io)document.querySelectorAll(".sec").forEach(x=>io.observe(x));
}
function pickOpt(id,i){optSel[id]=i;render()}
function chg(key,d){cart[key]=(cart[key]||0)+d;if(cart[key]<=0)delete cart[key];save();render();if(document.body.classList.contains("open")&&step==="cart")drawCart()}
function calc(){let n=0,sub=0;for(const k in cart){if(!byId[k.split("|")[0]]){delete cart[k];continue}n+=cart[k];sub+=cart[k]*unit(k)}
  const svc=orderType==="dine"?sub*.1:0, del=orderType==="delivery"&&sub>0?(sub>=60?0:5):0, gst=(sub+svc+del)*.09;
  return {n,sub,svc,del,gst,total:sub+svc+del+gst}}
function totals(){const c=calc();$("#cnt").textContent=$("#fcnt").textContent=c.n;$("#ctot").textContent=$("#ftot").textContent=money(c.total);$("#fab").classList.toggle("hide",!c.n)}
$("#member").onchange=e=>{member=e.target.checked;save();render()};

// nav highlight
var io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)document.querySelectorAll("nav a").forEach(a=>a.classList.toggle("on",a.dataset.k===e.target.id.slice(2)))}),{rootMargin:"-140px 0px -60% 0px"});

// ---- cart / checkout ----
let step="cart",orderType="dine",pay="paynow";
const PAYS=[
 ["paynow","PayNow","Pay from any Singapore bank app","#7b2d8e","PN"],
 ["card","Credit / Debit card","Visa · Mastercard · AMEX","#1a3d8f","CARD"],
 ["wallet","Apple Pay / Google Pay","Pay with your phone","#111","PAY"],
 ["grab","GrabPay","Pay with GrabPay wallet","#00b14f","GRAB"],
 ["cash","Cash / NETS at counter","Pay when you collect or after dining","#8a6d1d","$"],
];
function openCart(){step="cart";drawCart();document.body.classList.add("open")}
function closeCart(){document.body.classList.remove("open")}
function sums(c){return `<div class="sum"><span>Subtotal (${member?"member price":"U.P"})</span><span>${money(c.sub)}</span></div>
 ${c.svc?`<div class="sum"><span>Service charge 10%</span><span>${money(c.svc)}</span></div>`:""}
 ${orderType==="delivery"?`<div class="sum"><span>Delivery ${c.sub>=60?"(free over $60)":""}</span><span>${money(c.del)}</span></div>`:""}
 <div class="sum"><span>GST 9%</span><span>${money(c.gst)}</span></div><div class="sum tot"><span>Total</span><span>${money(c.total)}</span></div>`}
function drawCart(){const c=calc(),keys=Object.keys(cart);$("#dtitle").textContent="Your order";
  $("#db").innerHTML=keys.length?keys.map(k=>{const m=byId[k.split("|")[0]];return `<div class="line"><img src="/img/${m[6]}.jpg" alt=""><div class="t"><b>${m[1]} ${label(k)}</b><span class="en">${m[2]}</span><div>${money(unit(k))}</div></div>${ctrl(k)}</div>`}).join("")
   +`<label class="f" for="rem">Notes for the kitchen (spice level, allergies)</label><textarea id="rem" rows="2" placeholder="e.g. less spicy, no coriander">${notes}</textarea>`
   :`<div class="empty">Your cart is empty.<br>Add some Hunan favourites!</div>`;
  $("#df").innerHTML=keys.length?sums(c)+(openWin()?`<button class="big" onclick="toCheckout()">Checkout</button>`:closedHTML()+`<button class="big" disabled>Checkout</button>`):`<button class="big ghost" onclick="closeCart()">Browse menu</button>`;
  const r=$("#rem");if(r)r.oninput=e=>notes=e.target.value}
let notes="",form={name:"",phone:"",table:"",addr:"",time:"asap"};
// ordering hours, Singapore time (minutes after midnight)
const HOURS=[[690,870],[1050,1290]];
const tOverride=new URLSearchParams(location.search).get("now"); // e.g. ?now=15:00 for testing
function sgNow(){if(tOverride){const [h,m]=tOverride.split(":").map(Number);return h*60+m}const d=new Date(Date.now()+8*3600e3);return d.getUTCHours()*60+d.getUTCMinutes()}
function hm(m){const h=Math.floor(m/60),mm=m%60;return `${(h+11)%12+1}:${String(mm).padStart(2,"0")}${h<12?"am":"pm"}`}
function openWin(){const n=sgNow();return HOURS.find(([a,b])=>n>=a&&n<b)}
function nextOpen(){const n=sgNow(),w=HOURS.find(([a])=>a>n);return w?hm(w[0])+" today":hm(HOURS[0][0])+" tomorrow"}
function showHours(){const w=openWin(),el=$("#openpill");el.className="pill"+(w?"":" closed");el.textContent=w?"Open now · until "+hm(w[1]):"Closed · opens "+nextOpen()}
function closedHTML(){return `<div class="closedmsg">Online ordering is closed right now. We take orders 11:30am – 2:30pm and 5:30pm – 9:30pm. Next opening: <b>${nextOpen()}</b>.</div>`}
function toCheckout(){if(!openWin())return drawCart();step="checkout";drawCheckout()}
function drawCheckout(err){const c=calc();$("#dtitle").textContent="Checkout";
  const pm=PAYS.filter(p=>!(p[0]==="cash"&&orderType==="delivery"));if(!pm.find(p=>p[0]===pay))pay="paynow";
  $("#db").innerHTML=`
  <fieldset><legend>Order type</legend><div class="seg">
   ${[["dine","🍽️ Dine-in"],["pickup","🥡 Pickup"],["delivery","🛵 Delivery"]].map(([k,l])=>`<button class="pick ${orderType===k?"on":""}" onclick="setType('${k}')">${l}</button>`).join("")}</div></fieldset>
  <fieldset><legend>Your details</legend>
   <label class="f" for="fn">Name</label><input id="fn" value="${form.name}" autocomplete="name">
   <label class="f" for="fp">Mobile number</label><input id="fp" value="${form.phone}" inputmode="tel" autocomplete="tel" placeholder="8XXX XXXX">
   ${orderType==="dine"?`<label class="f" for="ft">Table number</label><input id="ft" value="${form.table}" inputmode="numeric">`:""}
   ${orderType==="delivery"?`<label class="f" for="fa">Delivery address</label><textarea id="fa" rows="2" autocomplete="street-address">${form.addr}</textarea>`:""}
   ${orderType!=="dine"?`<label class="f" for="fw">${orderType==="pickup"?"Pickup":"Delivery"} time</label><select id="fw"><option value="asap">As soon as possible (about 30 min)</option>${slots().map(s=>`<option ${form.time===s?"selected":""}>${s}</option>`).join("")}</select>`:""}
  </fieldset>
  <fieldset><legend>Payment method</legend><div class="pays">
   ${pm.map(p=>`<button class="pick ${pay===p[0]?"on":""}" onclick="setPay('${p[0]}')"><span class="ic" style="background:${p[3]}">${p[4]}</span><span><b>${p[1]}</b><br><span class="hint">${p[2]}</span></span></button>`).join("")}
  </div>
  </fieldset>${err?`<div class="err">${err}</div>`:""}`;
  $("#df").innerHTML=sums(c)+`<button class="big" onclick="placeOrder()">${pay==="cash"?"Place order":"Pay "+money(c.total)}</button><button class="big ghost" onclick="openCart()">Back to cart</button>`;
  totals()}
function keep(){const v=id=>$(id)?$(id).value:undefined;form.name=v("#fn")??form.name;form.phone=v("#fp")??form.phone;form.table=v("#ft")??form.table;form.addr=v("#fa")??form.addr;form.time=v("#fw")??form.time}
function setType(t){keep();orderType=t;drawCheckout()}
function setPay(p){keep();pay=p;drawCheckout()}
function slots(){const out=[];let t=Math.ceil((sgNow()+30)/15)*15;for(const [a,b] of HOURS){for(let m=Math.max(t,a);m<=b;m+=15)out.push(hm(m))}return out}
function placeOrder(){keep();
  if(!openWin()){step="cart";return drawCart()}
  if(!form.name.trim())return drawCheckout("Please enter your name.");
  if(!/^[689]\d{7}$/.test(form.phone.replace(/\D/g,"").replace(/^65/,"")))return drawCheckout("Please enter a valid Singapore mobile number.");
  if(orderType==="dine"&&!form.table.trim())return drawCheckout("Please enter your table number.");
  if(orderType==="delivery"&&!form.addr.trim())return drawCheckout("Please enter your delivery address.");
  const items=Object.entries(cart).map(([k,qty])=>{const [id,opt]=k.split("|");return {id,opt:+opt,qty}});
  $("#df").innerHTML=`<button class="big" disabled>Sending order…</button>`;
  fetch("/api/orders",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({items,member,type:orderType,
    name:form.name,phone:form.phone,table:form.table,address:form.addr,time:form.time,notes,payment:pay})})
  .then(r=>r.json().then(j=>({ok:r.ok,j}))).then(({ok,j})=>{
    if(!ok)return drawCheckout(j.error||"Something went wrong. Please try again.");
    cart={};notes="";save();totals();
    location.href=j.pay_url||j.status_url})            // provider payment page, or the order status page for cash
  .catch(()=>drawCheckout("Could not reach the restaurant. Check your connection and try again."))}
fetch("/api/menu").then(r=>r.json()).then(j=>{M=j.items.map(m=>[m.id,m.zh,m.en,m.mp,m.up,m.section,m.img,m]);byId=Object.fromEntries(M.map(m=>[m[0],m]));render()});showHours();setInterval(()=>{showHours();if(document.body.classList.contains("open")&&step==="cart")drawCart()},60e3);
