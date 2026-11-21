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
  function retailerOption(item) {
    // Host-and-scope validated; user still checks SKU, price and stock.
    if(!item || typeof item!=="object")return null;
    var retailer=String(item.retailer||"").toLowerCase();
    var hosts={amazon:["amazon.in","www.amazon.in"],
      flipkart:["flipkart.com","www.flipkart.com"],croma:["croma.com","www.croma.com"]};
    if(!hosts[retailer])return null;
    try {
      var parsed=new URL(String(item.url||""));
      if(parsed.protocol!=="https:"||parsed.username||parsed.password||
         !hosts[retailer].includes(parsed.hostname.toLowerCase()))return null;
      if(retailer==="amazon")parsed.searchParams.set("tag","guru07cc-21");
      var name={amazon:"Amazon",flipkart:"Flipkart",croma:"Croma"}[retailer];
      return {retailer:name,url:parsed.href,exact_model_link:item.exact_model_link===true,
        affiliate:retailer==="amazon"};
    } catch(_){return null;}
  }
  function retailerLinksFor(record) {
    return (Array.isArray(record&&record.retailer_links)?record.retailer_links:[])
      .map(retailerOption).filter(Boolean);
  }
  function retailLinksForAnswer(record,model) {
    return retailerLinksFor(record).map(function(item) {
      return {label:item.exact_model_link?
        item.retailer+" · matched model listing (check price and stock)":
        "Search "+item.retailer+" for "+model+" (not an exact listing)",
        url:item.url,affiliate:item.affiliate};
    });
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
    var ignored=/^(?:best|top|good|great|suggest|compare|recommend|recommendation|for|under|below|with|and|the|a|an|one|in|on|show|give|me|please|want|need|phone|mobile|tv|television|smart|earbuds?|earphones?|headphones?|tws|accessories|accessory|audio|charger|power|bank|buds|budget|cheap|low|price|buy|camera|battery|gaming|sound|anc|bluetooth|noise|cancel|cancelling|cancellation|display|led|oled|screen|inch|inches|quality|size|battery|life|speaker|speakers|wireless|charging|5g|4k)$/;
    var terms=query.split(" ").filter(function(t) {return t.length>1 && !ignored.test(t) && !/^\d{4,7}$/.test(t);});
    var bare=generic.test(query)||terms.length===0;
    var wantsAnc=/(?:noise\s+cancel|\banc\b|active\s+noise)/i.test(query);
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
      if(wantsAnc&&!/anc|noise cancel|adaptive noise/.test(fold((x.record.specifications||[]).filter(function(field){return sourceUrl(field.source_url);}).map(function(field){return field.label+" "+field.value;}).join(" "))))return false;
      if(bare)return true;
      if(!x.score)return false;
      if(terms.length>=2 && x.hits<terms.length)return false;
      if(exactNumbers.length && !x.hits)return false;
      return true;
    });
    choices.sort(function(a,b){return b.score-a.score||String(a.record.model).localeCompare(String(b.record.model));});
    return choices.slice(0,3).map(function(x){return x.record;});
  }
  // Exact model intent is separate from finding related research records. A request
  // for "iPhone 17" must never silently be answered as "iPhone 17 Pro".
  function requestedPhoneIdentity(request) {
    var phrase=fold(request && (request.baseQuery || request.raw) || "");
    if (/\b(?:compare|versus|vs)\b/.test(phrase)) return "";
    // "Apple mobile 17", "Apple 17" and "iPhone17" all refer to the
    // standard iPhone 17 unless the user explicitly says Pro, Max, etc.
    var apple=phrase.match(/\b(?:iphone\s*|apple\s+(?:(?:iphone|mobile|phone|smartphone)\s*)?)(\d{1,2}[a-z]?)(?:\s+(pro\s+max|pro|plus|max|mini|air))?(?=\s|$)/);
    if (apple) return "apple iphone "+apple[1]+(apple[2]?" "+apple[2]:"");
    var cleaned=phrase.replace(/\b(?:please|show|give|find|tell|me|i|want|need|a|the|best|top|good|suggest|recommend|for|with|camera|battery|gaming|display|storage|ram|price|model|models|buy|chahiye|batao|dikhao|hai|phone|mobile|smartphone)\b/g," ").replace(/\s+/g," ").trim();
    // Only infer a named model when brand AND a model identifier are explicit.
    // Broader brand/category searches keep the current evidence ordering.
    if (/^(?:samsung|google|oneplus|xiaomi|redmi|vivo|oppo|realme|motorola|poco|nothing|iqoo|lava|honor|hmd|nokia|infinix|tecno)\s/.test(cleaned) &&
        /\b(?:[a-z]{1,4}\d{1,4}[a-z]?|\d{1,3}[a-z]?)\b/.test(cleaned)) return cleaned;
    return "";
  }
  function classifyPhoneMatches(request,matches) {
    var identity=requestedPhoneIdentity(request);
    var entries=Array.isArray(matches)?matches:[];
    if (!identity) return {identity:"",exact:entries,related:[]};
    var exact=[],related=[];
    entries.forEach(function(item) {
      var card=item&&item.card||{};
      var brand=fold(card.brand),model=fold(card.model);
      var full=model.indexOf(brand+" ")===0?model:(brand+" "+model).trim();
      (full===identity?exact:related).push(item);
    });
    return {identity:identity,exact:exact,related:related};
  }
  var core={fold:fold,sourceUrl:sourceUrl,resultFields:resultFields,selectResearch:selectResearch,retailerOption:retailerOption,retailerLinksFor:retailerLinksFor,
    requestedPhoneIdentity:requestedPhoneIdentity,classifyPhoneMatches:classifyPhoneMatches};
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
      if(/^https:\/\//.test(l.url)){a.target="_blank";a.rel=(l.affiliate?"sponsored nofollow ":"")+"noopener noreferrer";}
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
    categoryPromise=fetch("/data/assistant_category_research.json",{credentials:"same-origin"})
      .then(function(response){if(!response.ok)throw Error("Category research unavailable");return response.json();})
      .then(function(payload){
        if(payload.mode!=="PUBLIC_RESEARCH_ASSISTANT_NO_OFFERS"||!Array.isArray(payload.records))throw Error("Invalid published catalogue");
        return payload.records;
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
      retailLinksForAnswer(rec,rec.brand+" "+rec.model).forEach(function(link){links.push(link);});
    });
    paragraphs.push("रिटेलर लिंक सिर्फ मॉडल के verified listing या saved search के लिए हैं; लाइव checkout price, stock, warranty और delivery की पुष्टि स्टोर पर ही करें। Amazon affiliate links पर Coupon World को commission मिल सकता है; कोई अतिरिक्त शुल्क नहीं।");
    if(!links.some(function(l){return l.label.includes("Amazon")||l.label.includes("Flipkart")||l.label.includes("Croma");})) paragraphs.push("इन मॉडल के लिए मौजूदा डेटा में सही retailer links नहीं हैं। वेबसाइट के TV/earbuds पेज पर उपलब्ध विकल्प देखें।");
    return {paragraphs:paragraphs,links:links};
  }
  function phoneReply(request,matches) {
    var condition=request.budget!==null?"₹"+request.budget.toLocaleString("en-IN")+" तक के dated-reference price band":"आपकी खोज";
    var groups=classifyPhoneMatches(request,matches);
    if(!matches.length) return {paragraphs:[condition+" के लिए मौजूदा मोबाइल रिसर्च में पुष्ट मिलान नहीं मिला। कोई मनगढ़ंत Top-3 या current price नहीं दिखाऊँगा।","फ़िल्टर बदलें या मौजूदा मोबाइल खोज के विस्तृत परिणाम देखें।"],links:[{label:"मोबाइल रिसर्च",url:"#mobileResearchSearch"}]};
    var status=document.getElementById("mobileResearchSearchStatus");
    var fallback=!!(status&&/no exact catalogue match/i.test(status.textContent));
    var paragraphs=[],links=[{label:"इन मोबाइलों के प्रमाण और फ़िल्टर देखें",url:"#mobileResearchSearch"}];
    if(groups.identity) {
      if(groups.exact.length) {
        paragraphs.push("सटीक मॉडल मिला: "+(groups.exact[0].card.brand||"")+" "+(groups.exact[0].card.model||"")+". नीचे इससे अलग मॉडल केवल संबंधित विकल्प के रूप में दिखेंगे।");
      } else {
        paragraphs.push("आपने "+groups.identity+" माँगा था, लेकिन उस सटीक मॉडल की पुष्टि इन खोज परिणामों में नहीं हुई। दूसरे मॉडल को वही फोन बताकर नहीं दिखाऊँगा।");
      }
    } else {
      paragraphs.push(fallback?"सटीक मिलान नहीं मिला; पास के documented मॉडल: ":"मौजूदा शोध में "+matches.length+" संबंधित मोबाइल मॉडल:");
    }
    var visible=groups.identity?groups.exact.slice(0,1).concat(groups.related.slice(0,2)):matches.slice(0,3);
    var shopping=root.CouponWorldMobileResearch;
    visible.forEach(function(item) {
      var card=item.card||{}, fields=resultFields(card,request.query,2);
      var name=((card.brand||"")+" "+(card.model||"")).trim();
      var isExact=!groups.identity||groups.exact.indexOf(item)>=0;
      paragraphs.push((groups.identity?(isExact?"सटीक मॉडल — ":"संबंधित विकल्प (अलग मॉडल) — "):"")+name+
        (fields.length?" — "+fields.map(function(f){return f.label+": "+f.value;}).join("; "):" — स्रोत-समर्थित विस्तृत विवरण अभी उपलब्ध नहीं है।"));
      // Never supply purchase links for a different model in an exact-model request.
      if(isExact&&shopping&&typeof shopping.retailerOptions==="function") {
        var choices=shopping.retailerOptions(card);
        choices.forEach(function(choice) {
          var safe=retailerOption({retailer:String(choice.retailer||"").toLowerCase(),url:choice.url,
            exact_model_link:choice.exact_model_link});
          if(safe)links.push({label:safe.exact_model_link?safe.retailer+" · exact-model listing for "+name+" (verify variant and price)":
            "Search "+safe.retailer+" for "+name+" (listing unverified)",
            url:safe.url,affiliate:safe.affiliate});
        });
      }
    });
    paragraphs.push("यह research coverage क्रम है, verified Top-3 खरीद सलाह नहीं। कीमत, स्टॉक और RAM/storage की पुष्टि स्टोर पर करें। केवल पहले से सहेजे गए मॉडल लिंक या retailer searches उपलब्ध हैं; Amazon affiliate links से Coupon World को commission मिल सकता है।");
    return {paragraphs:paragraphs,links:links};
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
