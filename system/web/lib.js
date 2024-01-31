// Création du handler du nav
ae(did("icon-menu"),'click',vFMobileNavOpen);  
function ae(el,eventName,cb){
 if(el.addEventListener)el.addEventListener(eventName,cb,false);
 else el['on'+eventName]=cb;
}
function de(el,eventName,cb){
 if(el.removeEventListener)el.removeEventListener(eventName,cb,false);
 else el.detachEvent('on'+eventName,cb);
}
function et(e){
 return(e.target||e.srcElement);
}
function did(s){ 
 return document.getElementById(s); 
}
function isIE(){
	var myNav=navigator.userAgent.toLowerCase();
	return(myNav.indexOf('msie')!=-1)? parseInt(myNav.split('msie')[1]): false;
}

function ajaxTO(type,url,data,cb,ftio,tio){
 //%%AP - 2021.10.05 - Désactivation du ping à chaque AJAX
 vFStopPing();
 
	var r,ie,t;
	url+='?a='+Date.now();
	if(ie=isIE()&&ie<10)r=new XMLDomainRequest();
	else r=new XMLHttpRequest();
	r.onreadystatechange=cb;
	r.ontimeout=ftio;
	r.onerror=ftio;
	r.open(type,url,true);
 // Si requete type post
 if(type=='POST')
  //Send the proper header information along with the request
  r.setRequestHeader('Content-type', 'application/x-www-form-urlencoded; charset=iso-8859-1');
	r.timeout=tio;
	r.send(data);
}
function getRandomInt(max) {
return Math.floor(Math.random() * max);
}

//----------------------------------------------------------------------------
// Gestion de l'ouverture du menu nav (mobile)
//----------------------------------------------------------------------------
function vFMobileNavOpen(e) {
 e=e?e:window.event;
 target=et(e);

 // Controle
 if(   ( target.id != did("icon-menu").id )
    && ( target.id != did("black").id )
    && ( target.id != did("nav-ul").id ) )return;
 // Ouverture de nav
 if(did("nav").classList.contains("close")) {
  did("nav").classList.remove("close");
  did("black").classList.remove("black-hide");
  // On bloque le scroll
  document.body.style.overflowY = "hidden";
  document.body.style.overflowX = "hidden";
  // Pour fermeture
  ae(did("black"),'click',vFMobileNavOpen);
  ae(did("nav-ul"),'click',vFMobileNavOpen);
 }
 // Fermeture du nav
 else{
  // Fermeture du nav
  did("nav").classList.add("close");
  did("black").classList.add("black-hide");
  // On réautorise le scroll
  document.body.style.overflowY = "visible";
  document.body.style.overflowX = "visible";
  // Pour fermeture
  de(did("black"),'click',vFMobileNavOpen);
  de(did("nav-ul"),'click',vFMobileNavOpen);
 }
}

//-------------------------------------------
// Classe requête AJAX
//-------------------------------------------
function AJAX_REQUEST( sReqType, sReqName, sReqData ){
 // Attribut constructeur
 this.sReqType = sReqType;
 this.sReqName = sReqName+'?a='+Date.now();
 this.sReqData = sReqData || '';
 // Attribut post-declaré
 this.xFCallback200   = undefined;
 this.xFCallback204   = undefined;
 this.vFCallbackError = undefined;
 this.xFCallbackUnknownCode  = undefined;
 this.xFCallbackEndOfRequest = undefined;
 this.uiTimeout = 12000;
 this.sErrorMsg = "";
 this.uiRetry   = 1; 
 this.bDontStopPing = false;
 
 var tAJAX_REQUEST = this;
 
 //---------------------------
 // Envoi de la requête
 //---------------------------
 this.vFSend = function(){
  var r,ie,t;
  //url+='?a='+Date.now();
  if(ie=isIE()&&ie<10)r=new XMLDomainRequest();
  else r=new XMLHttpRequest();
  r.onreadystatechange=this.vFResponseCallback;
  //r.ontimeout=this.vFTimeout;
  r.ontimeout=this.vFError;
  r.onerror=this.vFError;
  r.open(this.sReqType,this.sReqName,true);
  // Si requete type post : Send the proper header information along with the request
  if(this.sReqType=='POST') r.setRequestHeader('Content-type', 
                                      'application/x-www-form-urlencoded; charset=iso-8859-1');
  r.timeout=this.uiTimeout;
  // Conservation de la requête source dans l'objet XMLHttpRequest (création de propriété dans l'objet)
  r.ajaxObj = this;
  r.send(this.sReqData);
 }
 //---------------------------
 // Sur réponse à la requête
 //---------------------------
 this.vFResponseCallback = function(ea){
  ea=ea?ea:window.event;
  target=et(ea);
  // L'opération est terminée
  if(target.readyState!==4)return;
  if(target.status===200){
   //console.log("Response 200")
   // Si fonction bien définie
   if( this.ajaxObj.xFCallback200 != undefined ){
    this.ajaxObj.xFCallback200(ea)
   }
   else console.log("this.ajaxObj.xFCallback200 undefined")
  }
  else if(target.status===204){
   //console.log("Response 204")
   // Si fonction bien définie
   if( this.ajaxObj.xFCallback204 != undefined ){
    this.ajaxObj.xFCallback204(ea)
   }
   else console.log("this.ajaxObj.xFCallback204 undefined")
  }
  else if(target.status===404){
   //console.log("Response 404")
   // Si fonction bien définie
   if( this.ajaxObj.xFCallback404 != undefined ){
    this.ajaxObj.xFCallback404(ea)
   }
   else console.log("this.ajaxObj.xFCallback404 undefined")
  }
  else{
   //console.log("Unknown code")
   // Si fonction bien définie
   if( this.ajaxObj.xFCallbackUnknownCode != undefined ){
    this.ajaxObj.xFCallbackUnknownCode(ea)
   }
   else console.log("this.ajaxObj.xFCallbackUnknownCode undefined")
  }
  // Si fonction bien définie
  if( this.ajaxObj.xFCallbackEndOfRequest != undefined ){
   this.ajaxObj.xFCallbackEndOfRequest(ea)
  }
  else{/*console.log("this.ajaxObj.xFCallbackEndOfRequest undefined")*/}
 }
 //---------------------------
 // Timeout requête
 //---------------------------
 this.vFTimeout = function(e){
  e=e?e:window.event;e.target.abort();
  if(this.vFCallbackError) this.vFCallbackError(e);
 }
 //---------------------------
 // Erreur requête
 //---------------------------
 this.vFError = function(e){
  e=e?e:window.event;e.target.abort();
  console.log(this)
  //alert("this.ajaxObj.vFError")
  if( this.ajaxObj.uiRetry ){
   //alert("this.uiRetry")
   // Décrément
   this.ajaxObj.uiRetry = this.ajaxObj.uiRetry - 1; 
   var tAjaxObj = this.ajaxObj;
   // Relance avec temps aléatoire
   setTimeout(function(){tAjaxObj.vFSend()},200+getRandomInt(200));
  }
  else{
   if(this.ajaxObj.sErrorMsg!="") vFAlert(this.ajaxObj.sErrorMsg);
   if(this.ajaxObj.vFCallbackError) this.ajaxObj.vFCallbackError(e);
  }
 }
}
