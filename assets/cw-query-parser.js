/* Coupon World query modulation. Deterministic, local, and independent of paid AI APIs. */
(function (root) {
  "use strict";
  var wordNumbers = {
    "पांच":5,"पाँच":5,"दस":10,"पंद्रह":15,"पन्द्रह":15,"बीस":20,
    "पच्चीस":25,"तीस":30,"पैंतीस":35,"चालीस":40,"पचास":50,"साठ":60,
    "सत्तर":70,"अस्सी":80,"नब्बे":90,"सौ":100,
    "five":5,"ten":10,"fifteen":15,"twenty":20,"twenty five":25,
    "thirty":30,"forty":40,"fifty":50
  };
  var terms = [
    [/कैमरा/g,"camera"],[/बैटरी/g,"battery"],[/गेमिंग|खेलने/g,"gaming"],
    [/डिस्प्ले|स्क्रीन/g,"display"],[/रैम/g,"ram"],[/स्टोरेज/g,"storage"],
    [/सैमसंग/g,"samsung"],[/रेडमी/g,"redmi"],[/आईफोन/g,"iphone"],
    [/वनप्लस/g,"oneplus"],[/विवो/g,"vivo"],[/ओप्पो/g,"oppo"],
    [/मोबाइल|स्मार्टफोन|फ़ोन|फोन/g,"phone"],[/टीवी|टेलीविज़न|टेलीविजन/g,"tv"],
    [/ईयरबड्स|ईयरबड|इयरबड्स|इयरबड/g,"earbuds"],[/हेडफोन/g,"headphones"],
    [/चार्जर/g,"charger"],[/पावर बैंक|पावरबैंक/g,"power bank"],
    [/नहीं चाहिए/g,"nahi chahiye"],[/छोड़कर|छोड़कर/g,"exclude"],
    [/मुझे|बताओ|दिखाओ|चाहिए|कौन सा|कौनसे|के अंदर|के नीचे|से कम|वाला|वाले|में|का|की|के|और|ज़रा|जरा/g," "]
  ];
  function modulate(input, previous) {
    var raw=String(input == null ? "" : input).trim().slice(0,240);
    var memory=previous || {};
    var text=raw.toLowerCase().replace(/[०-९]/g,function(c){return String("०१२३४५६७८९".indexOf(c));})
      .replace(/,/g,"").replace(/हज़ार|हजार|हज़ार|hazaar|hazar|thousand/gi,"thousand")
      .replace(/लाख|lakh|lac/gi,"lakh");
    Object.keys(wordNumbers).sort(function(a,b){return b.length-a.length;}).forEach(function(word){
      var pattern=new RegExp("(^|\\s)"+word+"(?=\\s|$)","gi");
      text=text.replace(pattern,function(_,lead){return lead+wordNumbers[word];});
    });
    // Replace only number + explicit price magnitude, not TV sizes, RAM, or model names.
    text=text.replace(/(\d+(?:\.\d+)?)\s*(thousand|k)\b/g,function(_,n){return String(Number(n)*1000);})
      .replace(/(\d+(?:\.\d+)?)\s*lakh\b/g,function(_,n){return String(Number(n)*100000);});
    var explicitPhone=/\b(phone|mobile|smartphone|iphone|galaxy|pixel)\b|फ़ोन|फोन|मोबाइल/i.test(text);
    var explicitTv=/\b(tv|television|smart tv|mini led|oled tv|qled)\b|टीवी/i.test(text);
    var explicitAudio=/\b(earbuds?|earphones?|headphones?|tws|audio|buds)\b|ईयरबड/i.test(text);
    var explicitAccessory=/\b(charger|charging adapter|power bank|powerbank|accessor(?:y|ies))\b|चार्जर|पावरबैंक/i.test(text);
    var categories=[explicitPhone,explicitTv,explicitAudio,explicitAccessory].filter(Boolean).length;
    var category=categories>1?"all":explicitTv?"tvs":explicitAudio?"earbuds":explicitAccessory?"accessories":explicitPhone?"phones":(memory.category||"phones");
    terms.forEach(function(pair){text=text.replace(pair[0],pair[1]);});
    text=text.replace(/[?।!,]+/g," ").replace(/\s+/g," ").trim();
    var budget=null;
    var priceText=text.match(/(?:₹|rs\.?|inr|rupees|under|below|within|upto|up to|budget|price|maximum|less than)\s*(\d{4,7})\b/i);
    if(priceText) budget=Number(priceText[1]);
    else if (/^\s*\d{4,7}\b/.test(text) && /(?:phone|tv|earbuds|charger|battery|camera)/i.test(text))
      budget=Number(text.match(/^\s*(\d{4,7})/)[1]);
    else {
      var money=text.match(/\b(\d{4,7})\s*(?:rupees|tak|andar)\b/i);
      if(money) budget=Number(money[1]);
    }
    if(budget!==null && (budget<1000 || budget>1000000)) budget=null;
    var clearBudget=/\b(?:no budget|remove budget|any budget|forget budget)\b|बजट हटाओ/i.test(raw);
    if (clearBudget) budget=null;
    else if (budget===null && category===memory.category && memory.budget!=null) budget=memory.budget;
    var base=text.replace(/(?:₹|rs\.?|inr|rupees|under|below|within|upto|up to|budget|price|maximum|less than)\s*\d{4,7}\b/gi," ")
      .replace(/\b\d{4,7}\s*(?:rupees|tak|andar)\b/gi," ")
      .replace(/\b(?:please|tell|me|show|find|give|suggest|recommend|want|need|a|an|the|some|which|for|i|to|aur|batao|dikhao|chahiye|achha|accha|good)\b/gi," ")
      .replace(/\s+/g," ").trim();
    // A short follow-up can refine earlier intent without repeating the whole query.
    if(!explicitPhone && !explicitTv && !explicitAudio && !explicitAccessory &&
       memory.category===category && memory.baseQuery && /^(?:aur\s+)?(?:camera|battery|gaming|display|ram|storage|5g|ois)\b/i.test(base)) {
      base=(memory.baseQuery+" "+base).trim();
    }
    // Preserve explicit excluded brands; never weaken an identity or eligibility gate.
    var query=base;
    if(category==="phones") {
      if(!/\b(phone|mobile|smartphone|iphone|galaxy|pixel)\b/i.test(query)) query+=" phone";
      if(budget!==null) query+=" under "+budget;
    }
    query=query.replace(/\s+/g," ").trim().slice(0,240);
    return {raw:raw,category:category,budget:budget,baseQuery:base,query:query,
      isFollowUp:!!(memory.category && !categories),hasPriceConstraint:budget!==null};
  }
  root.CouponWorldQueryParser={modulate:modulate};
}(typeof window!=="undefined"?window:globalThis));
