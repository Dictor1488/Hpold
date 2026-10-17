(function () {
'use strict';
var root=document.getElementById('root');
var teams={left:document.getElementById('allies'),right:document.getElementById('enemies')};
var pools={left:[],right:[]},last='';
function px(n){return Math.round(n)+'px';}
function clamp(n,a,b){return Math.max(a,Math.min(b,n));}
function create(side,index){
 var pool=pools[side];
 while(pool.length<=index){
  var item=document.createElement('div');item.className='slot';
  var bar=document.createElement('div');bar.className='bar';
  var fill=document.createElement('div');fill.className='fill';bar.appendChild(fill);
  var label=document.createElement('div');label.className='label';
  item.appendChild(bar);item.appendChild(label);teams[side].appendChild(item);
  pool.push({element:item,fill:fill,label:label});
 }
 return pool[index];
}
function viewport(){
 return {width:Math.max(document.documentElement.clientWidth,window.innerWidth||0),
         height:Math.max(document.documentElement.clientHeight,window.innerHeight||0)};
}
function arrange(layout){
 var view=viewport(),w=view.width,h=view.height;
 if(!w||!h)return false;
 // Positions are explicit and resolution-scaled; no CSS custom variables
 // or default 0,0 anchor are permitted.
 var scale=clamp(h/1080,0.65,1.5),top=Math.round((layout.top||156)*scale);
 var inset=Math.round((layout.inset||310)*scale),rowHeight=Math.round((layout.rowHeight||24)*scale);
 var leftX=Math.max(0,Math.round(w/2-inset-104*scale));
 var rightX=Math.min(w-104*scale,Math.round(w/2+inset));
 Object.keys(teams).forEach(function(side){
  var team=teams[side];
  team.style.top=px(top);team.style.left=px(side==='left'?leftX:rightX);
  team.style.width=px(104*scale);
 });
 return {rowHeight:rowHeight,scale:scale};
}
function draw(force){
 var raw=window.model&&window.model.payload?String(window.model.payload):'{}';
 if(!force&&raw===last)return;
 last=raw;
 var data;try{data=JSON.parse(raw);}catch(e){root.style.display='none';return;}
 var geom=arrange(data.layout||{});
 if(!geom||!data.visible){root.style.display='none';return;}
 var rows=data.rows||[],seen={left:{},right:{}},hasRows=false;
 for(var i=0;i<rows.length;i++){
  var r=rows[i];
  if(!r||!pools[r.side]||typeof r.index!=='number'||r.index<0||r.index>29)continue;
  if(!r.show||Number(r.max)<=0)continue;
  var item=create(r.side,r.index),ratio=clamp(Number(r.current)/Number(r.max)||0,0,1);
  item.element.style.display='block';
  item.element.style.top=px(r.index*geom.rowHeight);
  item.element.style.transform='scale('+geom.scale+')';
  item.element.style.transformOrigin='top left';
  item.fill.style.width=px(72*ratio);
  item.label.textContent=String(r.current)+'/'+String(r.max);
  teams[r.side].className='team '+(r.side==='left'?'allies':'enemies')+(r.colorblind?' colorblind':'');
  seen[r.side][r.index]=true;hasRows=true;
 }
 Object.keys(pools).forEach(function(side){
  pools[side].forEach(function(item,index){if(!seen[side][index])item.element.style.display='none';});
 });
 root.style.display=hasRows?'block':'none';
}
function init(){
 try{if(typeof viewEnv!=='undefined'&&viewEnv.setHitTestEnabled)viewEnv.setHitTestEnabled(false);}catch(e){}
 if(window.engine){
  try{window.engine.on('viewEnv.onDataChanged',function(){draw(false);});}catch(e){}
  try{window.engine.on('self.onScaleUpdated',function(){draw(true);});}catch(e){}
 }
 if(typeof viewEnv!=='undefined'&&viewEnv.addDataChangedCallback){
  try{viewEnv.addDataChangedCallback(function(){draw(false);});}catch(e){}
 }
 window.addEventListener('resize',function(){draw(true);});
 window.setInterval(function(){draw(false);},200);
 draw(true);
}
if(window.engine&&window.engine.whenReady){
 window.engine.whenReady.then(init);
}else{init();}
}());
