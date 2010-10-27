/*
 * MFramework Core Ver 1.0
 * http://mframework.net/
 *
 * Copyright (c) 2009 Calidan Huang
 * GPL V2
*/
var ajaxLoadingText$="<font color=blue>L</font><small>oading...</small>";
var pageLoadingText$="<div style='padding:3px;background-color:white;width:70'>Loading...</div>";
var loadingBarCSS$="display:none;";
var insertData$="",DCFunc$=[],mTags$=[];


var nu$=navigator.userAgent;
var isIE=(navigator.appName.search(/Internet Explorer/i)>=0);
var isFirefox=(nu$.search("Firefox")>0);
var isChrome=(nu$.search("Chrome")>0);
var isSafari=(nu$.search("Safari")>0) && !isChrome;
var isOpera=(nu$.search("Opera")>0);


function MFInit(){
    document.write(pageLoadingText$+"<plaintext style='"+loadingBarCSS$+"'>");
    addEvent(window,'load',function(){
        var body$=document.getElementsByTagName('plaintext')[0].innerHTML;
        if(!isIE && !isFirefox)body$=body$.replace(/[&]lt;/g,'<').replace(/[&]gt;/g,'>').replace(/[&]amp;/g,'&');
        var i=body$.search(/<body/i);
        if(i!=-1)i=body$.indexOf(">",i)+1;
        setText(document.body,body$.substring(i));
    });
}

function echo(text){
    insertData$+=text;
}


function $(id){
    if(typeof id=="string")id=document.getElementById(id);
	return id;
}


function getValue(id){
    var o=$(id);
    if(o.type=="radio"){
        var kids=document.getElementsByTagName('input');
        for(var d=0;d<kids.length;d++){
            if(kids[d].type=="radio" && kids[d].name==o.name){
                if(kids[d].checked){
                    return kids[d].value;
                    break;
                }
            }
        }
        return "";
    }else if(o.type=="check")return o.checked;
    else if(!o.type){
        try{return o.contentWindow.document.body.innerHTML;}catch(e){}
    }
	return o.value;
}

function $r(id){
	var o=$(id);
    if(o)o.parentNode.removeChild(o);
}

function $c(tagName,pid){
    var nd=document.createElement(tagName),o=$(pid);
    if(o)o.appendChild(nd);
    return nd
}


function getSource(e){
	return e.srcElement?e.srcElement:e.target;
}

function addEvent(obj,action,func){
    obj=$(obj);
	if(obj.addEventListener){
		obj.addEventListener(action,func,false);
	}else{
		obj.attachEvent('on'+action,func);
	}
}



var onLoadFunc$=[],deep$=0;
function sText$(id,text,type,times){
    function cut(str,s,st,add){
        var q='',c,t,six,p,r=0;
        for(var i=st;i<str.length;i++){
            c=str.charAt(i);
            if(c=="<"){
                t=1;
                six=i+1;
                i++;
            }
            if(t){
                if((c==" " || c=='\n' || c=='>' || c=='/') && six>=0){
                    var ss=str.substring(six,i).toLowerCase();
                    if(!s){
                        if(ss=="br" || ss=='input' || ss=='img' || ss=='hr')p=1;
                        else if(ss.indexOf("/")<0)s=ss;
                    }else{
                        if(ss.indexOf("/")==0 && ss.substring(1)==s){
                            add--;
                            if(add==0){
                                s='';
                                p=1;
                                add=1;
                            }
                        }else if(ss==s)add++;
                    }
                    six=-1;
                }else if(c=='"' && q!="'")q=(q=='"')?'':'"';
                else if(c=="'" && q!='"')q=(q=="'")?'':"'";
                if(c==">" && q==''){
                    if(p){
                        r=i+1;
                        p=0;
                    }
                    t=0;
                }
            }else{
                var n=str.substring(i).indexOf("<");
                if(n>0)i+=n-1;
                else return {cp:r,tag:s,start:str.length-r,add:add};
            }
        }
        return {cp:r,tag:s,start:str.length-r,add:add};
    }
    var o=$(id);
    if(o!=null){
     	if(type<2 && o.tagName!='INPUT' && o.tagName!='TEXTAREA' && o.tagName!='IFRAME'){
            deep$++;
            if(!type)o.innerHTML="";
            var saveTag="",start=0,add=1,stop=0,tObj;
            for(var i=0;i<20000;i++){
                if(!o)return;
                tObj=changeMTag$(text);
                text=tObj.text;
                var cuter,cpt,cp,sinx=text.search(/<script>/i);
                if(!stop){
                    if(sinx>=0){
                        cuter=cut(text.substring(0,sinx),saveTag,start,add);
                        saveTag=cuter.tag;
                        start=cuter.start;
                        add=cuter.add;
                        cp=cuter.cp;
                    }else{
                        cuter=cut(text,saveTag,start,add);
                        saveTag=cuter.tag;
                        cp=text.length;
                        stop=1;
                    }
                    cpt=text.substring(0,cp).replace(/<@/g,"<");
                }else cpt=text.replace(/<@/g,"<");
                if(o.innerHTML=="")o.innerHTML+=cpt;
                else{
                    var tmp=$c("div"),fn;
                    tmp.innerHTML=cpt;
                    fn=tmp.firstChild;
                    while(fn){
                        o.appendChild(fn.cloneNode(true));
                        fn=fn.nextSibling;
                    }
                }
                if(stop)break;
                text=text.substring(cp);
                insertData$="";
                globalEval(text.substring(tObj.s-cp,tObj.e-cp).replace(/\r/g,''));
                text=text.substring(0,tObj.s-cp-8)+insertData$+text.substring(tObj.e-cp+9);
                insertData$="";
            }
            if(cpt){
                for(var e=0;e<onLoadFunc$.length;e+=2){
                    if(onLoadFunc$[e]==deep$){
                        onLoadFunc$[e+1]();
                        onLoadFunc$[e]=-1;
                    }
                }
                if(deep$==1)onLoadFunc$=[];
            }
            for(var k=0;k<DCFunc$.length;k++){
               DCFunc$[k]();
            }
            deep$--;
         }else{
            if(o.type=="radio"){
                var kids=document.getElementsByTagName('input');
                for(var d=0;d<kids.length;d++){
                    if(kids[d].type=="radio" && kids[d].name==o.name){
                        if(kids[d].value==text){
                            kids[d].checked=true;
                        }else{
                            kids[d].checked=false;
                        }
                    }
                }
            }else if(o.contentWindow){
                setTimeout(function(){
                    try{
                        if(isFirefox){
                            o.contentWindow.document.execCommand("inserthtml",false," ");
                            o.contentWindow.document.execCommand("undo",false,null);
                        }
                    }catch(e){}
                    o.contentWindow.document.body.innerHTML=text;
                },500);
          }else o.value=text;
         }
     }else if(times>0){
         setTimeout(function(){sText$(id,text,type,times-1)},50);
     }else $(id).innerHTML="Error";
}




function setText(id,text){
	sText$(id,text+"",0,20);
}

function setValue(id,text){
	sText$(id,text+"",2,20);
}


function addText(id,text){
	sText$(id,text,1,20);
}


function addDOMChangeEvent(f){
    DCFunc$.push(f);
}

function addOnLoadEvent(f){
    onLoadFunc$.push(deep$,f);
}

function getXmlHttpObject$(){
  var xmlHttp=null;
  try{xmlHttp=new XMLHttpRequest();}catch (e){
    try{xmlHttp=new ActiveXObject("Msxml2.XMLHTTP");}catch (e){
      xmlHttp=new ActiveXObject("Microsoft.XMLHTTP");}
    }
  return xmlHttp;
}



function globalEval(script){
    if(script=='')return;
    if (window.execScript)window.execScript(script);
    else if(isSafari){
        window.rcode=script;
        var scriptTag=$c('script');
        scriptTag.type='text/javascript';
        scriptTag.innerHTML='eval(window.rcode)';
        document.getElementsByTagName('head')[0].appendChild(scriptTag);
    }else window.eval(script);
}


function refresh(id,responsePage,func){
    var xmlHttpObj;
    if($(id)==null){
        xmlHttpObj=getXmlHttpObject$()
    }else{
        $(id).xmlHttpObj=getXmlHttpObject$();
        xmlHttpObj=$(id).xmlHttpObj;
    }
	xmlHttpObj.onreadystatechange=function(){
	if(xmlHttpObj.readyState==4){
      	if(xmlHttpObj.status==200){
            sText$(id,xmlHttpObj.responseText,0,20);
            if(func)func(xmlHttpObj.responseText);
	 	}else if($(id)!=null)if(id.innerHTML==ajaxLoadingText$)setText(id,"");
	}};
    xmlHttpObj.open("get",responsePage);
    xmlHttpObj.setRequestHeader("Content-Type","application/x-www-form-urlencoded");
    xmlHttpObj.send(null);
    setTimeout(function(){if(xmlHttpObj.readyState!=4){if($(id))setText(id,ajaxLoadingText$)}},1300);
}

function postFormData(formid,id,func){
       var c=$(formid).childNodes,i,str="";
       for(i=0;i<c.length;i++){
           if(c[i].value!=undefined && c[i].name!='' && c[i].tagName!="OPTION"){
               if(str.indexOf("&"+c[i].name+"=")<0)str+="&"+c[i].name+"="+encodeURIComponent(getValue(c[i]));
           }
       }
       postData($(formid).action,id,str,func);
}

function postData(page,id,data,func){
   var str='';
   if(typeof data=="string")str=data;
   else{
       var att;
       for(att in data){
           str+="&"+att+"="+encodeURIComponent(data[att]);
       }
   }
   var xmlHttpObj=getXmlHttpObject$();
   xmlHttpObj.onreadystatechange=function(){
       if(xmlHttpObj.readyState==4 && xmlHttpObj.status==200){
           sText$(id,xmlHttpObj.responseText,0,20);
           if(func)func(xmlHttpObj.responseText);
       }
   };
   xmlHttpObj.open("post",page);
   xmlHttpObj.setRequestHeader("Content-Type","application/x-www-form-urlencoded");
   xmlHttpObj.send(str);
}




function replaceString$(dataArray,struct){
    function setCharAt(str,index,c){
        if(index > str.length-1) return str;
        return str.substr(0,index)+c+str.substr(index+1);
    }
	var argNum=0;
	var finalString="";
	var replacedString="";
	for(var i=0;i<struct.length-1;i++){
		if(struct.substring(i,i+1)=="$" && struct.substring(i+1,i+2)=="$")struct=setCharAt(struct,i,'');
	}
	while(1){
		if(struct.indexOf("$"+argNum)>=0)argNum++;
		else break;
	}
	if(argNum==0)return struct;
	var count=-1;
    var r=(dataArray.length)/argNum;
	for(var k=0;k<r;k++){
		replacedString=struct;
		count++;
		for(i=argNum-1;i>=0;i--){
            var ix=i+k*argNum;
			if(ix>=dataArray.length)continue;
		    replacedString=replacedString.replace(/\$@/g,count).replace(/\$!/g,count+1).replace(/\$~/g,r);
            var rs=(dataArray[ix]+'').replace(/\$/g,"");
            replacedString=replacedString.replace(new RegExp("!\\$"+i,'g'),rs.replace(/</g,"&lt;").replace(/"/g,"&quot;").replace(/'/,"&#39;"));
		    replacedString=replacedString.replace(new RegExp("\\$"+i,'g'),rs.replace(/\n/g,"<br>"));
		}
		finalString+=replacedString;
	}
	return finalString.replace(//g,"$");
}

function setCSS(id,css){
    css=css.split(";");
    id=$(id);
    for(var i=0;i<css.length;i++){
        var av=css[i].split(":");
        av[0]=av[0].replace(/-[a-z]/g,function(s){return s.substring(1).toUpperCase()});
        if(css[i])id.style[av[0]]=av[1];
    }
}

function echof(dataArray,struct){
	echo(replaceString$(dataArray,struct));
}

function opacity(id,n){
  	if (n>=0||n<=100){
  		id=$(id);
        if(isIE){
            if(n==100)id.style.filter='';
            else id.style.filter="alpha(opacity='"+n+"')";
        }else{
            if(id.style.mozOpacity)id.style.mozOpacity=parseFloat(n/100);
            else id.style.opacity=parseFloat(n/100);
        }
    }
}

function gradual(obj,property,from,to,speed,interval,func,func2){
    obj=$(obj);
	interval=interval?interval:30;
	speed=speed?speed:2;
    var v;
    if(func2)v=func2(from);
    else v=from;
    if(property.toLowerCase()=="opacity")opacity(obj,v);
    else obj.style[property]=v;

    if((from+"").charAt(0)=="#"){
        var r=exp("0x"+from.substring(1,3)),g=exp("0x"+from.substring(3,5)),b=exp("0x"+from.substring(5,7));
        var r2=exp("0x"+to.substring(1,3)),g2=exp("0x"+to.substring(3,5)),b2=exp("0x"+to.substring(5,7));
        var stop=0;
        if(r-r2>=speed || r2-r>=speed){
            r+=speed*(r<r2?1:-1);
            stop++;
        }else r=r2;
        if(g-g2>=speed || g2-g>=speed){
            g+=speed*(g<g2?1:-1);
            stop++;
        }else g=g2;
        if(b-b2>=speed || b2-b>=speed){
            b+=speed*(b<b2?1:-1);
            stop++;
        }else b=b2;
        r=(r).toString(16);g=(g).toString(16);b=(b).toString(16);
        r=r.length<2?"0"+r:r,g=g.length<2?"0"+g:g,b=b.length<2?"0"+b:b;
        from="#"+r+g+b;

        if(stop>0){
            setTimeout(function(){gradual(obj,property,from,to,speed,interval,func,func2)},interval);
        }else{
            if(property)obj.style[property]=to;
            if(func)func();
        }
    }else{
        if(from-to>=speed || to-from>=speed){
            from-=speed*(from-to>0?1:-1);
            setTimeout(function(){gradual(obj,property,from,to,speed,interval,func,func2)},interval);
        }else{
            if(property.toLowerCase()=="opacity")opacity(obj,to);
            else obj.style[property]=to;
            if(func)func();
        }
    }
}


function changeMTag$(s){
    function addSlash(str){
        return str.replace(/\\/g,'\\\\').replace(/"/g,'\\"');
    }

    function getAtts(str,em){
        var an='',s=0,atts=[],stack=[];
        for(var p=0;p<str.length;p++){
            var cv=str.charAt(p);
            if(cv=="\\"){
                p++;
                continue;
            }
            switch(s){
                case 0:
                    if(cv=='='){
                        s=-2;
                        atts.push(an.replace(/[\r\n]/g,'').toLowerCase());
                        an='';
                    }else if((cv=='>' && em=='/') || (cv==em && str.charAt(p+1)=='>')){
                        atts.push(p,cv);
                        return atts;
                    }else if(cv!=' ')an+=cv;
                    else if(an!='')s=-1;
                    break;
                case -1:
                    if(cv=='='){
                        s=-2;
                        atts.push(an.replace(/[\r\n]/g,'').toLowerCase());
                        an='';
                    }else if((cv=='>' && em=='/') || (cv==em && str.charAt(p+1)=='>')){
                        atts.push(p,cv);
                        return atts;
                    }else if(cv!=' '){
                        an=cv;
                        s=0;
                    }
                break;
                case -2:
                    if(cv!=' '){
                        s=p;
                        if("\"'/[({".indexOf(cv)>=0)stack.push(cv);
                        else stack.push(' ');
                    }
                break;
                default:
                    var le=stack[stack.length-1];
                    if("\"'/".indexOf(le)>=0){
                        if(cv==le)stack.pop();
                    }else{
                        if("\"'[({".indexOf(cv)>=0)stack.push(cv);
                        else if(cv=="/" && le!=' ')stack.push(cv);
                        else if("])}".indexOf(cv)=="[({".indexOf(le) && "[({".indexOf(le)>=0)stack.pop();
                        else{
                            if(((cv==em && str.charAt(p+1)=='>') || (cv=='>' && em=='/')) && le==' '){
                                atts.push(str.substring(s,p),p,cv);
                                return atts;
                            }else if((cv==" " || '\r\n'.indexOf(cv)>=0) &&le==' '){
                                stack.pop();
                            }
                        }
                    }
                    if(stack.length==0){
                        atts.push(str.substring(s,p+1));
                        s=0;
                    }
                break;
            }
        }
        return [0];
    }


    function getP(str){
        var i=str.indexOf("=");
        if(i<0)return {n:str,d:"''"};
        else return {n:str.substring(0,i),d:str.substring(i+1)};
    }

    var minpos=-1,tagi=-1,inx,inner,ins,ins2,icount=0,ts=s,sarr=[],all=0;
    while(1){
        ins=ts.search(/<script>/i);
        ins2=ts.search(/<\/script>/i);
        if(ins2==-1 && ins==-1)break;
        if(ins<ins2 && ins>=0){
            sarr.push(all+ins);
            ts=ts.substring(ins+4);
            all+=ins+4;
            icount++;
        }else{
            if(icount>1)sarr.pop();
            else{
                sarr.push(all+ins2);
                break;
            }
            icount--;
            ts=ts.substring(ins2+4);
            all+=ins2+4;
        }
    }
    for(var i=0;i<mTags$.length;i++){
        var tn=mTags$[i][0],suffix="",n=tn.indexOf(','),em='/';
        if(n>0)tn=tn.substring(0,n);
        if(tn.charAt(tn.length-1)!="=")suffix="[\r\n />]";
        inx=s.search(new RegExp("<"+tn+suffix,"i"));
        if(inx==-1)continue;
          if(inx>sarr[0] && inx<sarr[1]){
              i++;
              continue;
          }
          if(minpos==-1 || inx<minpos){
              minpos=inx;
              tagi=i;
          }
      }
      if(sarr.length>1)if(minpos>sarr[1])return {text:s,s:sarr[0]+8,e:sarr[1]};
      if(tagi<0)return {text:s,s:sarr[0]+8,e:sarr[1]};
      inx=minpos;
      tn=mTags$[tagi][0];
      n=tn.indexOf(',');
      if(n>0){
          em=tn.substring(n+1);
          tn=tn.substring(0,n);
      }
      inx+=tn.replace(/\\/g,'').length+1;
      var inner2="",nObj='',ats=getAtts(s.substring(inx),em);

      if(ats[ats.length-1]==0)return {text:"<font color=red>Error:Missing '&gt;' after tag <b>&lt;"+tn+"</b></font>",s:0,e:0};
      else var inx2=ats[ats.length-2]+inx;
      for(var i2=2;i2<mTags$[tagi].length;i2++){
        var an=mTags$[tagi][i2],fd=getP(an).d;
        an=getP(an).n.toLowerCase();
        if(an=="inside"){
            var allArg=addSlash(s.substring(inx,inx2));
            if(allArg.replace(/ {0,}/,"")=="")allArg=fd?fd:'""';
            else allArg='"'+allArg+'"';
            inner2+=','+allArg.replace(/[\n\r]/g,"\\n");
        }else if(an=='events'){
            var leng=ats.length-2,ae='';
            for(var h=0;h<leng;h+=2){
                if(ats[h].search(/onclick|onmouse|onkey|onblur|onfocus/)>=0){
                    ae+=ats[h]+"="+ats[h+1];
                }
            }
            if(ae=='')ae=fd;
            inner2+=",\""+addSlash(ae)+'"';
        }else{
            if(an=='name')nObj="new ";
            var len=ats.length-2,a=0;
            for(var g=0;g<len;g+=2){
                if(an==ats[g]){
                    inner2+=","+ats[g+1];
                    if(an=='name')nObj="var "+ats[g+1].substring(1,ats[g+1].length-1)+"=new ";
                    a=1;
                    break;
                }
            }
            if(!a){
                inner2+=","+fd;
                if(an=='name' && fd!="''"){
                    nObj=exp(fd)+"="+nObj;
                }
            }
        }
    }
    ts=s.substring(inx2);
    var inx3,inx4;
    if(em!="/" || ats[ats.length-1]=="/" || ts.search(new RegExp("</"+tn+">","i"))<0){
        inner="";
        inx4=inx2;
        if(s.charAt(inx2)!=">")inx4+=1;
    }else{
        var afs=0,sp,ep,sc=0;
        while(1){
           sp=ts.search(new RegExp("<"+tn+suffix,"i"));
           ep=ts.search(new RegExp("</"+tn+">","i"));
           if((sp<ep || ep<0) && sp>=0){
               var att=getAtts(ts.substring(sp+tn.length),em);
               if(att[att.length-1]!="/")sc++;
               ts=ts.substring(sp+3);
               afs+=sp+3;
           }else if((sp>ep || sp<0) && ep>=0){
               if(sc==0)break;
               else sc--;
               ts=ts.substring(ep+3);
               afs+=ep+3;
           }else if(sp==-1 && ep==-1 && sc>=0){
               afs-=3;
               break;
           }else break;
        }
        inx3=afs+ep;
        inx4=s.indexOf(">",inx3+inx2);
        inner=s.substring(inx2+1,inx3+inx2);
    }
    
    var scp="<script>"+nObj+mTags$[tagi][1]+'("'+addSlash(inner).replace(/[\n\r]/g,"\\n")+'"'+inner2.replace(/[\n\r]/g,"")+');</script>';
    s=s.substring(0,minpos)+scp+s.substring(inx4+1);
    return {text:s,s:minpos+8,e:minpos+scp.length-9};
}



function createTag(){
    arguments[0]=arguments[0].toLowerCase().replace(/([\?\+\*\{\}\[\]])/g,'\\$1');
    for(var i=0;i<mTags$.length;i++){
        if(mTags$[i][0].toLowerCase()==arguments[0]){
            mTags$[i]=arguments;
            return;
        }
    }
    mTags$.push(arguments);
}

function removeTag(tagName){
    for(var i=0;i<mTags$.length;i++){
        if(mTags$[i][0].search(new RegExp(tagName,"i"))>=0)mTags$=mTags$.slice(0,i).concat(mTags$.slice(i+1));
    }
}

function exp(v$){
    var tmp;
    try{
    eval("tmp="+v$+";");
    }catch(e){return "undefined"}
    return tmp;
}

function echoTag$(innerHTML,all){
    echo(exp(all)+"");
}
createTag("=","echoTag$","inside");

function echofTag$(innerHTML,data,template,emptyDataText){
    if(template.length!=0)echof(data,template);
    else echof(data,innerHTML);
    if(data.length==0)echo(emptyDataText);
}
createTag("echof","echofTag$","data","template","emptyDataText");