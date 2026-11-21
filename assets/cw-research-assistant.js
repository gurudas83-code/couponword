/* Coupon World on-site research assistant: uses existing evidence, no remote LLM, no invented prices. */
(function (root) {
  "use strict";
  var parser=root.CouponWorldQueryParser;
  function fold(value) {
    return String(value == null ? "" : value).toLocaleLowerCase("en-IN")
      .replace(/[^a-z0-9\u0900-\u097f]+/g," ").replace(/\s+/g," ").trim();
  }
  function sourceUrl(value) {
    try {
      var url=new URL(String(value||""));
      return url.protocol==="https:" && url.hostname && !url.username && !url.password ? url.href : "";
    } catch (_) {return "";}
  }
  function topic(query) {
    var s=fold(query);
    if (/camera|कैमरा|photo/.test(s)) return /camera|कैमरा|photo/;
    if (/battery|बैटरी|backup|charging/.test(s)) return /battery|playback|charging|mah|power|बैटरी/;
    if (/gaming|game|गेमिंग|refresh|120hz/.test(s)) return /gpu|chipset|refresh|hz|gaming|hdmi/;
    if (/anc|noise|sound|audio|bass|कैंसिल/.test(s)) return /noise|anc|sound|audio|driver|codec/;
    if (/size|inch|इंच/.test(s)) return /size|inch|panel/;
    if (/software|os|update/.test(s)) return /software|os|update|android/;
    return null;
  }
  function resultFields(record, query, max) {
    var specs=record&&record.specifications||[];
    var entries=Array.isArray(specs) ? specs :
      Object.keys(specs).map(function(key){var item=specs[key];return {label:key.replace(/_/g," "),value:item&&item.value,source_url:item&&item.source_url};});
    var relevant=topic(query);
    return entries.filter(function(item) {
      return item && item.value!=null && String(item.value).trim() && sourceUrl(item.source_url);
    }).sort(function(a,b){
      return Number(Boolean(relevant&&relevant.test(String(b.label))))-Number(Boolean(relevant&&relevant.test(String(a.label))));
    }).slice(0,max||3).map(function(item) {
      return {label:String(item.label||"Specification"),value:String(item.value),url:sourceUrl(item.source_url)};
    });
  }
  function eligibleRecord(record, category) {
    if (!record || !record.model || !record.brand) return false;
    if(category==="tvs")return record.category==="tvs";
    if(category==="earbuds")return record.category==="earbuds"||
      (record.category==="accessories"&&/earbud|earphone|tws/i.test(record.product_type||record.model));
    if(category==="accessories")return record.category==="accessories";
    return record.category==="tvs"||record.category==="earbuds"||record.category==="accessories";
  }
  function selectResearch(records, request, category) {
    var query=fold(request.baseQuery||request.query||"");
    var generic=/^(?:tv|television|smart tv|earbuds?|earphones?|headphones?|tws|accessories|accessory|charger|power bank|phone|mobile|audio|buds|बड्स|टीवी)?$/;
    var ignored=/^(?:best|top|good|great|suggest|compare|recommend|recommendation|for|under|below|with|and|the|a|an|one|in|on|show|give|me|please|want|need|phone|mobile|tv|television|smart|earbuds?|earphones?|headphones?|tws|accessories|accessory|audio|charger|power|bank|buds|budget|cheap|low|price|buy|camera|battery|gaming|sound|anc|bluetooth|noise|cancel|display|led|oled|screen|inch|inches|quality|size|battery|life|speaker|speakers|wireless|charging|5g|4k)$/;
    var terms=query.split(" ").filter(function(t) {return t.length>1 && !ignored.test(t) && !/^\d{4,7}$/.test(t);});
    var bare=generic.test(query)||terms.length===0;
    var exactNumbers=terms.filter(function(t){return /^\d{2,3}$/.test(t);});
    // Size and product-code matches must be real: never reinterpret 55-inch as a budget.
    var choices=(records||[]).filter(function(x){return eligibleRecord(x,category);}).map(function(record){
      var name=fold(record.brand+" "+record.model+" "+(record.model_code||"")+" "+(record.manufacturer_model_code||""));
      var specText=fold((record.specifications||[]).map(function(s){return s.label+" "+s.value;}).join(" "));
      var hits=terms.filter(function(t){return name.split(" ").includes(t)||name.includes(t)||(/^\d{2,3}$/.test(t)&&specText.includes(t+" "));});
      var score=hits.length*10+(name.includes(query)&&query.length>2?25:0)+
        (terms.some(function(t){return fold(record.brand).includes(t);})?2:0);
      return {record:record,score:score,hits:hits.length};
    }).filter(function(x){
      // A named model / brand request must not be silently replaced with unrelated products.
      if(bare)return true;
      if(!x.score)return false;
      if(terms.length>=2 && x.hits<terms.length)return false;
      if(exactNumbers.length && !x.hits)return false;
      return true;
    });
    choices.sort(function(a,b){return b.score-a.score||String(a.record.model).localeCompare(String(b.record.model));});
    return choices.slice(0,3).map(function(x){return x.record;});
  }
  var core={fold:fold,sourceUrl:sourceUrl,resultFields:resultFields,selectResearch:selectResearch};
  root.CouponWorldAssistantCore=core;
  if(typeof document==="undefined")return;
  var host=document.getElementById("cwAssistant");
  var chat=document.getElementById("cwAssistantMessages");
  var form=document.getElementById("cwAssistantForm");
  var input=document.getElementById("cwAssistantInput");
  var microphone=document.getElementById("cwAssistantMic");
  var voiceToggle=document.getElementById("cwAssistantSpeak");
  var voiceLanguage=document.getElementById("cwAssistantLanguage");
  var notice=document.getElementById("cwAssistantNotice");
  if(!host||!chat||!form||!input||!parser)return;
  var session=null,turn=0,pending=false,recognizer=null;
  var categoryPromise=null;
  function append(role,paragraphs,links) {
    var item=document.createElement("div");
    item.className="cw-assistant-message "+(role==="user"?"cw-assistant-user":"cw-assistant-bot");
    var label=document.createElement("strong");label.textContent=role==="user"?"You":"Coupon World research";item.appendChild(label);
    (paragraphs||[]).forEach(function(p){
      var text=document.createElement("p");text.textContent=p;item.appendChild(text);
    });
    (links||[]).filter(function(l){return l&&l.url;}).forEach(function(l){
      var a=document.createElement("a");a.textContent=l.label+" ↗";a.href=l.url;
      if(/^https:\/\//.test(l.url)){a.target="_blank";a.rel="noopener noreferrer";}
      item.appendChild(a);
    });
    chat.appendChild(item);
    while(chat.children.length>13)chat.removeChild(chat.firstChild);
    chat.scrollTop=chat.scrollHeight;
    return item;
  }
  function respond(paragraphs, links) {
    append("bot",paragraphs,links);
    if(voiceToggle&&voiceToggle.checked&&root.speechSynthesis&&root.SpeechSynthesisUtterance) {
      root.speechSynthesis.cancel();
      var utterance=new root.SpeechSynthesisUtterance(paragraphs.join(". ").slice(0,450));
      utterance.lang=voiceLanguage.value||"hi-IN";
      root.speechSynthesis.speak(utterance);
    }
  }
  function catalogue() {
    if(categoryPromise)return categoryPromise;
    categoryPromise=Promise.all([
      fetch("/data/category_research_verified.json",{credentials:"same-origin"}).then(function(r){if(!r.ok)throw Error("category research unavailable");return r.json();}),
      fetch("/data/india_tv_earbuds_40_catalogue.json",{credentials:"same-origin"}).then(function(r){if(!r.ok)throw Error("TV/audio research unavailable");return r.json();})
    ]).then(function(payloads){
      if(!Array.isArray(payloads[0].records)||!Array.isArray(payloads[1].records))throw Error("Invalid catalogue");
      var joined=payloads[1].records.slice();
      var known=new Set(joined.map(function(x){return fold(x.brand+" "+x.model);}));
      payloads[0].records.forEach(function(x){
        var key=fold(x.brand+" "+x.model);
        if(!known.has(key)){joined.push(x);known.add(key);}
      });
      return joined;
    }).catch(function(e){categoryPromise=null;throw e;});
    return categoryPromise;
  }
  function overviewReply(request, matches) {
    var paragraphs=[];
    var links=[];
    if(request.budget!==null)paragraphs.push("₹"+request.budget.toLocaleString("en-IN")+" बजट पूछा गया है। टीवी, ईयरबड्स और एक्सेसरीज़ के लिए यहाँ विश्वसनीय लाइव कीमत उपलब्ध नहीं है; नीचे दिखे मॉडल बजट-अनुकूल होने की पुष्टि नहीं हैं।");
    if(!matches.length) {
      paragraphs.push("इस शर्त के लिए प्रकाशित कैटलॉग में पर्याप्त मिलान नहीं मिला। मैं कोई मॉडल या कीमत बनाकर नहीं बताऊँगा।");
      return {paragraphs:paragraphs,links:[{label:"टीवी रिसर्च",url:"/tvs/"},{label:"एक्सेसरी रिसर्च",url:"/accessories/"}]};
    }
    paragraphs.push("प्रकाशित रिसर्च में "+matches.length+" संबंधित मॉडल मिले। ये दस्तावेज़ी तथ्य हैं, प्रमाणित performance ranking नहीं।");
    matches.forEach(function(rec) {
      var fields=resultFields(rec,request.query,2);
      paragraphs.push(rec.brand+" "+rec.model+(fields.length?" — "+fields.map(function(f){return f.label+": "+f.value;}).join("; "):" — स्रोत-समर्थित तकनीकी जानकारी अभी सीमित है।"));
      var url=sourceUrl(rec.source_url)||fields[0]&&fields[0].url;
      if(url)links.push({label:rec.brand+" "+rec.model+" — research source",url:url});
    });
    paragraphs.push("आज की कीमत, स्टॉक, warranty और exact model code retailer पर जाँचें; अलग-अलग स्रोतों के दावों को independent testing न मानें।");
    return {paragraphs:paragraphs,links:links};
  }
  function phoneReply(request,matches) {
    var condition=request.budget!==null?"₹"+request.budget.toLocaleString("en-IN")+" तक के dated-reference price band":"आपकी खोज";
    if(!matches.length)return {paragraphs:[condition+" के लिए मौजूदा मोबाइल रिसर्च में पुष्ट मिलान नहीं मिला। कोई मनगढ़ंत Top-3 या current price नहीं दिखाऊँगा।","फ़िल्टर बदलें या मौजूदा मोबाइल खोज के विस्तृत परिणाम देखें।"],links:[{label:"मोबाइल रिसर्च",url:"#mobileResearchSearch"}]};
    var status=document.getElementById("mobileResearchSearchStatus");
    var fallback=!!(status&&/no exact catalogue match/i.test(status.textContent));
    var paragraphs=[(fallback?"सटीक मिलान नहीं मिला; पास के documented मॉडल: ":"मौजूदा शोध में "+matches.length+" संबंधित मोबाइल मॉडल: ")];
    matches.slice(0,3).forEach(function(item) {
      var card=item.card||{},fields=resultFields(card,request.query,2);
      var name=(card.brand||"")+" "+(card.model||"");
      paragraphs.push(name.trim()+(fields.length?" — "+fields.map(function(f){return f.label+": "+f.value;}).join("; "):" — विवरण के लिए स्रोत देखें।"));
    });
    paragraphs.push("यह research coverage क्रम है, verified Top-3 खरीद सलाह नहीं। बजट में केवल dated price references उपयोग होते हैं; current price और उपलब्धता retailer पर जाँचें।");
    return {paragraphs:paragraphs,links:[{label:"इन मोबाइलों के प्रमाण और फ़िल्टर देखें",url:"#mobileResearchSearch"}]};
  }
  async function ask(value) {
    var raw=String(value||"").trim().slice(0,240);
    if(!raw||pending)return;
    pending=true;
    input.value="";
    append("user",[raw]);
    var local=++turn;
    var request=parser.modulate(raw,session);
    session=request;
    try {
      if(/^(?:hi|hello|नमस्ते|हैलो|help|मदद|what can you do|क्या कर सकते हो)[?!. ]*$/i.test(raw)) {
        respond(["नमस्ते! मैं Coupon World की अपनी रिसर्च से मोबाइल, टीवी, ईयरबड्स और एक्सेसरीज़ के बारे में हिंदी या अंग्रेज़ी में जवाब देता हूँ।","उदाहरण: 'पंद्रह हजार में कैमरा फोन', '55 inch Xiaomi TV', या 'noise cancelling earbuds'। मैं लाइव कीमत या अनदेखी समीक्षा नहीं गढ़ता।"]);
      } else if(request.category==="phones") {
        var research=root.CouponWorldMobileResearch;
        if(!research||typeof research.search!=="function") {
          respond(["मोबाइल सर्च अभी उपलब्ध नहीं है; कृपया नीचे मौजूदा मोबाइल रिसर्च देखें।"],[{label:"मोबाइल खोज",url:"#mobileResearchSearch"}]);
        } else {
          var matches=research.search(request.query);
          var status=document.getElementById("mobileResearchSearchStatus");
          // Core catalogue fetch starts on page load; do not make a duplicate fetch.
          if(!matches.length&&status&&/loading|लोड|research unavailable/i.test(status.textContent)) {
            var retries=0;
            while(retries<24&&local===turn) {
              await new Promise(function(resolve){setTimeout(resolve,150);});
              matches=research.search(request.query);
              if(matches.length||!/loading|लोड/i.test(status.textContent))break;
              retries++;
            }
          }
          if(local===turn) {var phone=phoneReply(request,matches||[]);respond(phone.paragraphs,phone.links);}
        }
      } else {
        var records=await catalogue();
        if(local===turn){
          var categories=request.category==="all"?["tvs","earbuds","accessories"]: [request.category];
          var chosen=[];
          categories.forEach(function(category){
            selectResearch(records,request,category).forEach(function(record){
              if(!chosen.includes(record))chosen.push(record);
            });
          });
          var result=overviewReply(request,chosen.slice(0,3));
          respond(result.paragraphs,result.links);
        }
      }
    } catch (_) {
      if(local===turn)respond(["मौजूदा रिसर्च फ़ाइल अभी नहीं खुल पा रही है। मैंने कोई विकल्प या कीमत अनुमान से नहीं बनाई।"],[{label:"कैटेगरी देखें",url:"/tvs/"},{label:"मोबाइल शोध",url:"#mobileResearchSearch"}]);
    } finally {
      pending=false;
    }
  }
  form.addEventListener("submit",function(event){event.preventDefault();ask(input.value);});
  document.querySelectorAll("[data-cw-assistant-example]").forEach(function(button){
    button.addEventListener("click",function(){input.value=button.getAttribute("data-cw-assistant-example")||"";ask(input.value);});
  });
  var Recognition=root.SpeechRecognition||root.webkitSpeechRecognition;
  if(!Recognition) {
    microphone.disabled=true;
    microphone.title="Voice recognition is unsupported in this browser. Type your question instead.";
    if(notice)notice.textContent="Text chat works on all supported browsers. Microphone needs browser speech recognition and your permission.";
  } else {
    microphone.addEventListener("click",function(){
      if(recognizer){recognizer.stop();return;}
      try {
        recognizer=new Recognition();
        recognizer.lang=voiceLanguage.value||"hi-IN";
        recognizer.interimResults=false;
        recognizer.maxAlternatives=1;
        recognizer.onresult=function(e){
          var words=e.results&&e.results[0]&&e.results[0][0]&&e.results[0][0].transcript;
          if(words){input.value=String(words).slice(0,240);ask(input.value);}
        };
        recognizer.onerror=function(e){if(notice)notice.textContent="माइक से सुनना संभव नहीं हुआ ("+(e.error||"unknown")+"). आप लिखकर पूछ सकते हैं।";};
        recognizer.onend=function(){recognizer=null;microphone.setAttribute("aria-pressed","false");microphone.textContent="🎙 बोलें";};
        recognizer.start();microphone.setAttribute("aria-pressed","true");microphone.textContent="■ रोकें";
        if(notice)notice.textContent="Listening with your browser's speech service. Audio handling depends on your browser; Coupon World does not store recordings.";
      } catch(_) {
        recognizer=null;
        if(notice)notice.textContent="यह ब्राउज़र माइक्रोफोन चालू नहीं कर सका। कृपया लिखें।";
      }
    });
  }
  root.CouponWorldAssistant={ask:ask};
}(typeof window!=="undefined"?window:globalThis));
