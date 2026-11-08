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
const M = [
 ["hunan","湖南小炒肉","Hunan Stir-Fried Pork",18.8,20.9,"sig","hunan-stir-fried-pork",{badge:"桌桌<br>必点",hero:1}],
 ["lemon","手打柠檬茶","Handcrafted Fresh Lemon Tea",3.9,3.9,"sig","handcrafted-fresh-lemon-tea",{note:"解腻解辣最佳搭档"}],
 ["ybeef","菜园子小炒黄牛肉","Cai Yuan Zi Stir-fried Yellow Beef",20.8,23.9,"sig","cai-yuan-zi-stir-fried-yellow-beef"],
 ["bass","跳水鲈鱼","Steamed Sea Bass with Chili Sauce",32.8,35.9,"sig","steamed-sea-bass-with-chili-sauce"],
 ["gingerchk","老姜小炒鸡","Stir-fried Chicken with Old Ginger",18.8,20.9,"sig","stir-fried-chicken-with-old-ginger"],
 ["fishhead","菜园子剁椒鱼头","CaiYuanZi Steamed Fish Head with Chopped Chili",18.8,20.9,"garden","cai-yuan-zi-steamed-fish-head-with-chopped-chili"],
 ["eel","爆炒鳝鱼","Stir-fried Eel",36.8,38.9,"garden","stir-fried-eel"],
 ["tofu","红烧豆腐煲","Braised Tofu in Clay Pot",15.9,18.9,"garden","braised-tofu-in-clay-pot"],
 ["feet","蒜香凤爪","Garlic Chicken Feet",17.8,19.8,"garden","garlic-chicken-feet"],
 ["brisket","番茄烧牛腩","Braised Beef Brisket with Tomato",20.8,23.9,"garden","braised-beef-brisket-with-tomato"],
 ["sourfish","金汤酸菜鱼","Sour Fish in Golden Broth",32.8,35.9,"garden","sour-fish-in-golden-broth"],
 ["egg","擂辣椒皮蛋","Mashed Green Peppers with Preserved Egg",9.8,11.9,"cold","mashed-green-peppers-with-preserved-egg"],
 ["camellia","茶油辣椒","Chili in Camellia Oil",8.8,9.9,"cold","camellia-oil-chili"],
 ["cucumber","刀拍黄瓜","Smashed Cucumber",7.8,9.9,"cold","smashed-cucumber"],
 ["veggs","网红醋溜蛋","Vinegar-Braised Eggs",13.8,15.9,"rice","vinegar-braised-eggs",{badge:"下饭<br>必点"}],
 ["spshrimp","椒盐香辣虾","Salt & Pepper Spicy Shrimp",24.8,26.9,"rice","salt-and-pepper-spicy-shrimp",{badge:"特色<br>推荐"}],
 ["duck","菜园子酱板鸭","Caiyuanzi Spiced Dry-Pressed Duck",17.8,18.9,"rice","old-changsha-spiced-salted-duck",{opts:[["Half 半只",17.8,18.9],["Whole 1只",29.9,32.8]]}],
 ["radish","萝卜干炒腊肉","Stir-fried Dried Radish with Preserved Pork",22.8,23.9,"rice","stir-fried-dried-radish-with-preserved-pork"],
 ["bullfrog","香辣跳跳蛙","Spicy Bullfrog",29.8,32.9,"rice","spicy-bullfrog"],
 ["liver","土匪猪肝","Bandit-Style Sautéed Pork Liver",18.8,20.9,"rice","bandit-style-sauteed-pork-liver"],
 ["squid","干锅鱿鱼须","Dry Pot Squid Tentacles",18.8,21.9,"rice","dry-pot-squid-tentacles"],
 ["fhtofu","鱼头豆腐煲","Fish Head & Tofu Casserole",18.8,20.9,"chef","fish-head-and-tofu-casserole",{badge:"特色<br>必点",hero:1}],
 ["cornshrimp","玉米青豆滑虾仁","Tender Shrimp with Corn and Green Peas",17.8,19.9,"chef","tender-shrimp-with-corn-and-green-peas"],
 ["trotter","梅干菜烧猪蹄","Braised Pork Trotters with Preserved Mustard Greens",27.8,29.9,"chef","braised-pork-trotters-with-preserved-mustard-greens"],
 ["noodles","酸包菜炒米粉","Stir-fried Rice Noodles with Sour Cabbage",12.8,13.9,"chef","stir-fried-rice-noodles-with-sour-cabbage"],
 ["curedmush","干锅腊肉鹿茸菇","Dry Pot Cured Pork with Velvet Mushrooms",22.9,23.8,"chef","dry-pot-cured-pork-with-velvet-mushrooms"],
 ["gshrimp","蒜蓉粉丝虾","Garlic Shrimp with Vermicelli",18.8,20.9,"steam","garlic-shrimp-with-vermicelli"],
 ["culter","大白刁","Grilled White Culter Fish",29,32,"steam","grilled-white-culter-fish"],
 ["segg","肉沫蒸蛋","Steamed Egg with Minced Pork",11.8,13.9,"steam","steamed-egg-with-minced-pork"],
 ["kelp","鲜海带肉丸汤","Fresh Kelp Meatball Soup",17.8,19.9,"soup","fresh-kelp-meatball-soup"],
 ["lsoup","湖藕筒子骨汤","Lotus Root & Pork Knuckle Soup",21.8,23.9,"soup","lotus-root-and-pork-knuckle-soup"],
 ["cauli","大碗花菜","Large Bowl Braised Cauliflower",13.8,14.9,"veg","large-bowl-braised-cauliflower"],
 ["lettuce","油麦菜","Sautéed Leaf Lettuce",11.8,13.9,"veg","sauteed-leaf-lettuce"],
 ["scab","手撕包菜","Shredded Cabbage Stir-Fry",12.8,13.9,"veg","shredded-cabbage-stir-fry"],
 ["zucc","家常丝瓜","Homemade Zucchini",12.8,14.9,"veg","homemade-zucchini"],
 ["lstem","小炒莴笋丝","Stir-fried Shredded Lettuce Stem",12.8,13.9,"veg","stir-fried-shredded-lettuce-stem"],
 ["potato","酸辣土豆丝","Sour & Spicy Shredded Potatoes",12.8,14.9,"veg","sour-and-spicy-shredded-potatoes",{note:"清炒 plain stir-fry available"}],
 ["sprouts","韭菜胖豆芽","Stir-fried Bean Sprouts with Chinese Chives",11.8,13.9,"veg","stir-fried-bean-sprouts-with-chinese-chives"],
 ["ricecake","糖油粑粑","Sugar Oil Glutinous Rice Cakes",10.8,11.9,"dim","sugar-oil-glutinous-rice-cakes",{note:"6 pcs 六个一份"}],
 ["pumpkin","南瓜饼","Pumpkin Pancakes",11.8,12.9,"dim","pumpkin-pancakes",{note:"6 pcs 六个一份"}],
];
// beverages: [id, 中文, English, price, group, slug]
const D = [
 ["tiger","虎牌啤酒","Tiger Beer",8.6,"啤酒 Beer","tiger-beer"],
 ["carls","皇帽啤酒","Carlsberg",9.6,"啤酒 Beer","carlsberg-beer"],
 ["tsing","青岛啤酒","Tsingtao Beer",9,"啤酒 Beer","tsingtao-beer"],
 ["wusu","乌苏啤酒","Wusu Beer",9,"啤酒 Beer","wusu-beer"],
 ["moutai","飞天茅台 500ml","Fei Tian Moutai",388,"白酒 Spirits","fei-tian-moutai-500ml"],
 ["egt100","红星二锅头 100ml","Hongxing Erguotou",15.5,"白酒 Spirits","hongxing-erguotou-100ml"],
 ["egt500","红星二锅头 500ml","Hongxing Erguotou",66.5,"白酒 Spirits","hongxing-erguotou-500ml"],
 ["water","矿泉水","Mineral Water",2,"饮料 Soft Drinks","mineral-water"],
 ["wlk","王老吉","Wong Lo Kat",2.8,"饮料 Soft Drinks","wong-lo-kat"],
 ["coke","可口可乐（糖/无糖）","Coca-Cola (regular / zero)",2.8,"饮料 Soft Drinks","coca-cola"],
 ["sprite","雪碧","Sprite",2.8,"饮料 Soft Drinks","sprite"],
];
D.forEach(d=>M.push([d[0],d[1],d[2],d[3],d[3],"drink",d[5],{group:d[4]}]));

const $=s=>document.querySelector(s), money=n=>"$"+n.toFixed(2);
const byId=Object.fromEntries(M.map(m=>[m[0],m]));
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
  return `<article class="card"><div class="ph"><img loading="lazy" src="img/${img}.jpg" alt="${en}">${ex.badge?`<span class="badge">${ex.badge}</span>`:""}</div>
  <div class="info"><div class="row"><div><div class="zh">${zh}</div><div class="en">${en}</div></div>${priceHTML(p[1],p[2])}</div>
  ${ex.opts?`<div class="opts">${ex.opts.map((x,i)=>`<button class="${i==o?"on":""}" onclick="pickOpt('${id}',${i})">${x[0]}</button>`).join("")}</div>`:""}
  <div class="add"><span class="note">${ex.note||""}</span>${ctrl(id+"|"+(ex.opts?o:0))}</div></div></article>`}
function ctrl(key){const q=cart[key]||0;return q?`<span class="qty"><button onclick="chg('${key}',-1)" aria-label="Remove one">−</button><b>${q}</b><button onclick="chg('${key}',1)" aria-label="Add one">+</button></span>`
  :`<button class="plus" onclick="chg('${key}',1)">+ Add</button>`}

function render(){
  let h="";for(const k in S){const items=M.filter(m=>m[5]===k);
    h+=`<section class="sec" id="s-${k}"><div class="banner"><h2>${S[k][0]}</h2><em>${S[k][1]}</em></div>`;
    if(k==="drink"){const g={};items.forEach(m=>(g[m[7].group]??=[]).push(m));
      h+=`<div class="drinks">${Object.entries(g).map(([n,l])=>`<div class="dcol"><h3>${n}</h3>${l.map(m=>`<div class="drow"><img loading="lazy" src="img/${m[6]}.jpg" alt=""><div class="t"><b>${m[1]}</b><span class="en">${m[2]}</span></div><span class="p">$${m[4].toFixed(2)}</span>${ctrl(m[0]+"|0")}</div>`).join("")}</div>`).join("")}</div>`}
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
 ["paynow","PayNow QR","Scan with any Singapore bank app","#7b2d8e","PN"],
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
  $("#db").innerHTML=keys.length?keys.map(k=>{const m=byId[k.split("|")[0]];return `<div class="line"><img src="img/${m[6]}.jpg" alt=""><div class="t"><b>${m[1]} ${label(k)}</b><span class="en">${m[2]}</span><div>${money(unit(k))}</div></div>${ctrl(k)}</div>`}).join("")
   +`<label class="f" for="rem">Notes for the kitchen (spice level, allergies)</label><textarea id="rem" rows="2" placeholder="e.g. less spicy, no coriander">${notes}</textarea>`
   :`<div class="empty">Your cart is empty.<br>Add some Hunan favourites!</div>`;
  $("#df").innerHTML=keys.length?sums(c)+(openWin()?`<button class="big" onclick="toCheckout()">Checkout</button>`:closedHTML()+`<button class="big" disabled>Checkout</button>`):`<button class="big ghost" onclick="closeCart()">Browse menu</button>`;
  const r=$("#rem");if(r)r.oninput=e=>notes=e.target.value}
let notes="",form={name:"",phone:"",table:"",addr:"",time:"asap",cn:"",ce:"",cc:""};
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
  </div>${pay==="card"?`<div class="two" style="margin-top:8px"><div style="grid-column:1/-1"><label class="f" for="cn">Card number</label><input id="cn" value="${form.cn}" inputmode="numeric" autocomplete="cc-number" placeholder="1234 5678 9012 3456"></div><div><label class="f" for="ce">Expiry</label><input id="ce" value="${form.ce}" placeholder="MM/YY" autocomplete="cc-exp"></div><div><label class="f" for="cc">CVC</label><input id="cc" value="${form.cc}" inputmode="numeric" autocomplete="cc-csc"></div></div>`:""}
  </fieldset>${err?`<div class="err">${err}</div>`:""}`;
  $("#df").innerHTML=sums(c)+`<button class="big" onclick="placeOrder()">${pay==="cash"?"Place order":"Pay "+money(c.total)}</button><button class="big ghost" onclick="openCart()">Back to cart</button>`;
  totals()}
function keep(){const v=id=>$(id)?$(id).value:undefined;form.name=v("#fn")??form.name;form.phone=v("#fp")??form.phone;form.table=v("#ft")??form.table;form.addr=v("#fa")??form.addr;form.time=v("#fw")??form.time;form.cn=v("#cn")??form.cn;form.ce=v("#ce")??form.ce;form.cc=v("#cc")??form.cc}
function setType(t){keep();orderType=t;drawCheckout()}
function setPay(p){keep();pay=p;drawCheckout()}
function slots(){const out=[];let t=Math.ceil((sgNow()+30)/15)*15;for(const [a,b] of HOURS){for(let m=Math.max(t,a);m<=b;m+=15)out.push(hm(m))}return out}
function placeOrder(){keep();
  if(!openWin()){step="cart";return drawCart()}
  if(!form.name.trim())return drawCheckout("Please enter your name.");
  if(!/^[689]\d{7}$/.test(form.phone.replace(/\D/g,"").replace(/^65/,"")))return drawCheckout("Please enter a valid Singapore mobile number.");
  if(orderType==="dine"&&!form.table.trim())return drawCheckout("Please enter your table number.");
  if(orderType==="delivery"&&!form.addr.trim())return drawCheckout("Please enter your delivery address.");
  if(pay==="card"){const n=form.cn.replace(/\s/g,"");if(!/^\d{13,19}$/.test(n)||!/^\d\d\/\d\d$/.test(form.ce)||!/^\d{3,4}$/.test(form.cc))return drawCheckout("Please check your card details.")}
  const c=calc(),no="CYZ"+Date.now().toString().slice(-6);
  if(pay==="paynow"){$("#dtitle").textContent="Scan to pay";
    $("#db").innerHTML=`<div class="ok"><p>Scan this PayNow QR with your banking app</p>${qrSVG(no)}<p><b>${money(c.total)}</b> · Ref <b>${no}</b></p><p class="hint">The order is sent to the kitchen once payment is received.</p></div>`;
    $("#df").innerHTML=`<button class="big" onclick="done('${no}')">I've paid</button><button class="big ghost" onclick="toCheckout()">Change method</button>`;return}
  $("#df").innerHTML=`<button class="big" disabled>Processing…</button>`;setTimeout(()=>done(no),pay==="cash"?200:1200)}
function done(no){const c=calc(),t={dine:"Dine-in · Table "+form.table,pickup:"Pickup · "+(form.time==="asap"?"ASAP":form.time),delivery:"Delivery · "+(form.time==="asap"?"ASAP":form.time)}[orderType];
  $("#dtitle").textContent="Order placed";
  $("#db").innerHTML=`<div class="ok"><div class="tick">✓</div><h2>谢谢! Thank you, ${form.name}</h2><p>Order <b>${no}</b><br>${t}</p><p>${pay==="cash"?"Please pay "+money(c.total)+" at the counter.":"Paid "+money(c.total)+" via "+PAYS.find(p=>p[0]===pay)[1]+"."}</p><p class="hint">Questions? Call 6041 9403</p></div>`;
  $("#df").innerHTML=`<button class="big" onclick="closeCart()">Back to menu</button>`;cart={};notes="";form.cn=form.ce=form.cc="";save();render()}
// decorative QR-style placeholder (replace with the restaurant's real PayNow QR)
function qrSVG(seed){let h=0;for(const ch of seed)h=(h*31+ch.charCodeAt(0))>>>0;const n=25;let r="";
  for(let y=0;y<n;y++)for(let x=0;x<n;x++){const f=(x<7&&y<7)||(x>17&&y<7)||(x<7&&y>17);h=(h*1103515245+12345)>>>0;
    const on=f?(x%18===0||x%18===6||y%18===0||y%18===6||(x%18>1&&x%18<5&&y%18>1&&y%18<5)):(h>>16)&1;if(on)r+=`<rect x="${x}" y="${y}" width="1" height="1"/>`}
  return `<svg class="qr" viewBox="0 0 ${n} ${n}" fill="#111">${r}</svg>`}

render();showHours();setInterval(()=>{showHours();if(document.body.classList.contains("open")&&step==="cart")drawCart()},60e3);
