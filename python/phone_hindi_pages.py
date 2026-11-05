"""Hindi editorial mirror of approved phone guides and source-linked model research.

This publication layer does not change ranking, product identity, commerce or offers.
Budget pages are intentionally noindex until there are audited Top-3 results.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

from python.phone_research_pages import (
    EDITORIAL_MODEL_KEYS, accepted_specs, eligible, model_title, slug_for,
)

SITE = "https://coupon-world.in"
ROOT = Path(__file__).resolve().parents[1]
HUB = "/hi/guides/phone-budget-guides/"
PHONE_HUB = "/hi/phones/"
BUDGET_HUB = "/hi/budgets/"
BUDGETS = tuple(range(10000, 100001, 5000))

# Editorially written Hindi guides, in exact one-to-one order with the
# existing vetted English subjects. Never auto-translate manufacturer values.
GUIDE_COPY = {
 "phones-under-10000": ("₹10,000 तक का फोन कैसे चुनें", [
  ("रोज़मर्रा की ज़रूरत", "कॉल, संदेश, डिजिटल भुगतान, पढ़ाई और नेविगेशन के लिए फोन लेते समय पहले अपनी ज़रूरी ऐप्स की सूची बनाएं। कम कीमत वाला फोन तभी उपयोगी है जब आवश्यक ऐप्स ठीक से चलें, स्क्रीन पढ़ने योग्य हो और पर्याप्त वास्तविक स्टोरेज उपलब्ध हो।"),
  ("सही मेमोरी समझें", "विक्रेता के विज्ञापन में लिखी कुल RAM वास्तविक भौतिक RAM और वर्चुअल RAM का जोड़ हो सकती है। निर्माता के भारत वाले मॉडल की RAM, स्टोरेज, 4G/5G नेटवर्क, चार्जर और वारंटी को वास्तविक लिस्टिंग से मिलाएं।"),
  ("बजट की वास्तविक सीमा", "हमारे मौजूदा अंग्रेज़ी शॉर्टकट में ₹5,000 से ₹10,000 से कम के पुराने मूल्य-संदर्भ का उपयोग होता है। इसे आज की बिक्री कीमत न मानें। किसी फोन का परिणाम न दिखना उसकी बाजार में अनुपलब्धता का प्रमाण नहीं है।")]),
 "phones-under-15000": ("₹15,000 तक फोन चुनने की जाँच-सूची", [
  ("कौन-सी समस्या हल करनी है", "फोन बार-बार चार्ज करना पड़ता है, ऐप बदलते समय धीमा होता है या स्टोरेज जल्दी भर जाती है—पहले अपनी सबसे बड़ी समस्या पहचानें। केवल बड़ी बैटरी या अधिक मेगापिक्सल बेहतर उपयोग-अनुभव की गारंटी नहीं हैं।"),
  ("एक ही वेरिएंट की तुलना", "हर दुकान पर समान RAM और स्टोरेज वाला मॉडल देखें। बैंक कार्ड, एक्सचेंज और सदस्यता से मिलने वाली छूट को आधार कीमत के समान न मानें। इन शर्तों का लाभ न मिलने पर वास्तविक भुगतान अलग होगा।"),
  ("पुराने मूल्य का सावधानी से उपयोग", "संबंधित अंग्रेज़ी गाइड ₹10,000 से ₹15,000 से कम के संदर्भ-बैंड से जुड़ी है। पुराने संदर्भ केवल खोज को सीमित करने के लिए हैं; उपलब्धता, आज की कीमत और डिलीवरी विक्रेता से जाँचें।")]),
 "phones-under-20000": ("₹20,000 तक संतुलित स्मार्टफोन", [
  ("प्राथमिकता से खोजें", "एक ही फोन कैमरा, गेमिंग और बैटरी में सर्वोत्तम हो, यह आवश्यक नहीं। फोटो और वीडियो के लिए वास्तविक नमूने, गेमिंग के लिए टिकाऊ फ्रेम रेट तथा दैनिक काम के लिए स्टोरेज और सॉफ़्टवेयर सहायता की जाँच करें।"),
  ("मॉडल के नाम में अंतर", "समान नाम वाले 4G, 5G, Pro और सामान्य संस्करण अलग हो सकते हैं। सही मॉडल नंबर, प्रोसेसर तथा भारत में बेचे जाने वाले RAM/स्टोरेज संयोजन को निर्माता की वेबसाइट से मिलाएं।"),
  ("संदर्भ, निश्चित प्रस्ताव नहीं", "पुराने रिसर्च संदर्भ ₹15,000 से ₹20,000 से कम के बैंड के लिए हैं। बैंक छूट या सेल कीमत बदल सकती है; इस पेज से किसी आज के ऑफर का दावा नहीं किया जा रहा।")]),
 "phones-under-30000": ("₹30,000 तक फोन: सही प्राथमिकता", [
  ("कैमरा, बैटरी या गेमिंग", "खरीदने से पहले तय करें कि आपकी पहली प्राथमिकता क्या है। कैमरा-केंद्रित और गेमिंग-केंद्रित शॉर्टलिस्ट अलग हो सकती हैं। केवल किसी फीचर के मौजूद होने से उसे स्वतंत्र परीक्षण में विजेता नहीं कहा जा सकता।"),
  ("डिवाइस के प्रमाण", "कैमरा के लिए कम रोशनी, चलती वस्तु और वीडियो के परीक्षण देखें। गेमिंग के लिए तापमान तथा लंबे समय का फ्रेम रेट देखें। बैटरी के लिए समान परीक्षण-पद्धति पर वास्तविक रनटाइम उपयोगी है।"),
  ("तय बजट में सही संस्करण", "₹25,000 से ₹30,000 से कम का रिसर्च-बैंड पुराने कीमत-संदर्भ पर आधारित है। सटीक भारतीय वेरिएंट और विक्रेता की अंतिम भुगतान राशि अलग से देखें।")]),
 "phones-under-50000": ("₹50,000 तक प्रीमियम फोन के सवाल", [
  ("बड़ी कीमत, बड़ी अपेक्षा", "इस स्तर पर डिस्प्ले, कैमरा स्थिरीकरण, अपडेट नीति, नेटवर्क संगतता और दीर्घकालिक विश्वसनीयता के प्रमाण तलाशें। बड़े ब्रांड या ऊँची कीमत को अपने आप बेहतर प्रदर्शन का प्रमाण न मानें।"),
  ("परीक्षण के तरीके की तुलना", "अलग-अलग वेबसाइटों के बैटरी या कैमरा स्कोर बिना एक जैसी परीक्षण-पद्धति के सीधे तुलनीय नहीं होते। परीक्षण की तारीख, सॉफ़्टवेयर संस्करण और उपयोग की गई डिवाइस भी पढ़ें।"),
  ("खरीदने से पहले", "अंग्रेज़ी शॉर्टकट का संदर्भ ₹45,000 से ₹50,000 से कम है। मौजूदा कीमत, एक्सचेंज, वारंटी, अधिकृत विक्रेता और स्टॉक को भुगतान से पहले स्वतंत्र रूप से जाँचें।")]),
 "camera-phone-buying-guide": ("अच्छे कैमरा फोन के प्रमाण", [
  ("सिर्फ मेगापिक्सल पर्याप्त नहीं", "सेंसर, लेंस, इमेज प्रोसेसिंग और स्थिरीकरण तस्वीर की गुणवत्ता प्रभावित करते हैं। 200MP लिखा होने से फोटो स्वतः बेहतर नहीं होती। मूल आकार के दिन और रात के नमूने तुलना में मदद करते हैं।"),
  ("फोटो और वीडियो अलग जाँचें", "त्वचा के रंग, गतिमान विषय, पोर्ट्रेट, अल्ट्रावाइड और वीडियो स्थिरता जैसे उपयोगों को अलग देखें। किसी एक पद्धति के स्कोर को सभी प्रकार की फोटोग्राफी का अंतिम निर्णय न मानें।"),
  ("प्रमाण का स्रोत", "मॉडल की तकनीकी जानकारी के लिए निर्माता और प्रदर्शन के लिए एक समान विधि वाले स्वतंत्र परीक्षण देखना बेहतर है। जहाँ तुलना योग्य परीक्षण नहीं है, वहाँ कैमरा रैंकिंग लंबित रखना अधिक विश्वसनीय है।")]),
 "battery-phone-buying-guide": ("बैटरी फोन में वास्तविक बैकअप", [
  ("mAh और चलने का समय अलग हैं", "बैटरी क्षमता केवल ऊर्जा-संग्रह का संकेत देती है। स्क्रीन, नेटवर्क, चिपसेट, तापमान और ऐप्स के उपयोग से वास्तविक बैकअप बदलता है। अधिक mAh हमेशा अधिक घंटों की गारंटी नहीं है।"),
  ("तुलनीय रनटाइम खोजें", "एक जैसी ब्राइटनेस, नेटवर्क परिस्थिति और उपयोग-पैटर्न में हुए स्वतंत्र परीक्षणों की तुलना करें। स्टैंडबाय समय और सक्रिय स्क्रीन उपयोग को एक ही आँकड़ा न मानें।"),
  ("चार्जिंग का दूसरा पहलू", "निर्माता द्वारा बताए गए वॉट, वास्तविक चार्ज समय, संगत चार्जर तथा बैटरी की दीर्घकालिक देखभाल को अलग-अलग जाँचें। बिना मापे हुए रनटाइम को सर्वश्रेष्ठ कहना उचित नहीं है।")]),
 "gaming-phone-buying-guide": ("गेमिंग फोन में FPS और तापमान", [
  ("प्रोसेसर के नाम से आगे", "चिपसेट एक शुरुआत है, पूरा गेमिंग अनुभव नहीं। एक ही खेल में ग्राफिक्स सेटिंग, लंबे समय का FPS और फ्रेम टाइम देखना ज़रूरी है। शुरुआती बेंचमार्क लगातार गेमिंग की स्थिरता नहीं बताता।"),
  ("गर्मी और बैटरी", "कई मिनट के बाद थ्रॉटलिंग, हाथ में गर्मी, चार्जिंग के दौरान प्रदर्शन और बैटरी खर्च मायने रखते हैं। अलग-अलग परीक्षण कक्ष और गेम संस्करण के नतीजे सीधे एक-जैसे नहीं होते।"),
  ("सटीक मॉडल की शर्त", "RAM/स्टोरेज वेरिएंट, सॉफ़्टवेयर अपडेट और भारत में मिलने वाले मॉडल की पुष्टि करें। जब पर्याप्त तुलनीय गेमिंग प्रमाण न हों, हमारी Top-3 रैंकिंग प्रकाशित नहीं की जाएगी।")]),
 "phone-display-buying-guide": ("फोन की स्क्रीन समझें", [
  ("मापना क्या है", "आकार के साथ रेजोल्यूशन, पैनल प्रकार, अधिकतम रिफ्रेश रेट और बाहर धूप में पठनीयता देखें। विज्ञापन की पीक ब्राइटनेस और रोज़मर्रा की फुल-स्क्रीन चमक एक जैसी नहीं होती।"),
  ("आराम और उपयोग", "टेक्स्ट स्पष्टता, रंग, HDR समर्थन, ऑटो ब्राइटनेस और फ्लिकर संवेदनशीलता अलग पहलू हैं। केवल AMOLED या 120Hz लिखा होना पूरे डिस्प्ले की गुणवत्ता का प्रमाण नहीं है।"),
  ("मूल स्रोत", "निर्माता की सूची से घोषित विशेषताओं की पुष्टि करें। स्वतंत्र माप उपलब्ध हों तो प्रकाश-स्थिति और परीक्षण-पद्धति के साथ पढ़ें; अलग विधि वाले निट्स को बराबर न मानें।")]),
 "phone-software-support-guide": ("फोन की बची हुई सॉफ़्टवेयर सहायता", [
  ("लॉन्च और अपडेट में अंतर", "कंपनी के बताये OS अपग्रेड और सुरक्षा अपडेट अलग चीजें हैं। कुल वर्षों की घोषणा को फोन की आज से बची सहायता अवधि न समझें; आरंभ तिथि या अंतिम समर्थन तारीख खोजें।"),
  ("भारत का मॉडल देखें", "क्षेत्र और मॉडल के आधार पर सॉफ़्टवेयर रिलीज़ तथा उपलब्ध सुविधाएँ बदल सकती हैं। निर्माता की आधिकारिक क्षेत्रीय जानकारी से सटीक मॉडल का समर्थन जाँचें।"),
  ("भविष्य का जोखिम", "कम कीमत वाला पुराना फोन खरीदते समय शेष सुरक्षा अपडेट, मरम्मत और उपयोग की अवधि पर विचार करें। बिना स्रोत के किसी मॉडल के भविष्य के अपडेट का अनुमान न लगाएँ।")]),
 "phone-build-reliability-guide": ("फोन की बनावट और विश्वसनीयता", [
  ("IP रेटिंग को सही समझें", "निर्माता द्वारा घोषित धूल/पानी की IP रेटिंग एक निर्धारित प्रयोगशाला परीक्षण से संबंधित होती है। इसे हर परिस्थिति में वाटरप्रूफ होने की गारंटी न मानें।"),
  ("रोज़मर्रा के जोखिम", "स्क्रीन सुरक्षा, फ्रेम, बटन, गर्मी, सॉफ़्टवेयर समर्थन, मरम्मत और वारंटी को साथ देखें। केवल धातु या ग्लास की मौजूदगी से टिकाऊपन साबित नहीं होता।"),
  ("दावा और परीक्षण", "निर्माता की विशेषताओं को स्वतंत्र ड्रॉप या दीर्घकालिक विश्वसनीयता परीक्षण का विकल्प न समझें। जहाँ ऐसा प्रमाण नहीं है, सीमा स्पष्ट बताना जरूरी है।")]),
 "physical-ram-vs-virtual-ram": ("वास्तविक RAM और वर्चुअल RAM", [
  ("भौतिक RAM क्या है", "डिवाइस में लगी वास्तविक RAM और स्टोरेज का इस्तेमाल करके बनाई गई अतिरिक्त वर्चुअल RAM समान नहीं हैं। दोनों के प्रदर्शन और विलंबता की तुलना सीधे संख्याएँ जोड़कर न करें।"),
  ("विज्ञापन कैसे पढ़ें", "विक्रेता की 8GB+8GB लिखावट का अर्थ अक्सर 8GB भौतिक RAM और 8GB विस्तार होता है, न कि 16GB वास्तविक RAM। सही वेरिएंट निर्माता की वेबसाइट और रिटेलर की कॉन्फ़िगरेशन से मिलाएं।"),
  ("फैसले के दूसरे कारण", "उपयोग होने वाली ऐप्स, स्टोरेज गति, सॉफ़्टवेयर और कीमत को भी देखना चाहिए। Coupon World किसी अनुमानित RAM संख्या को प्रमाणित वेरिएंट नहीं मानता।")]),
 "128gb-vs-256gb-phone-storage": ("128GB या 256GB स्टोरेज", [
  ("अपनी फाइलों का अनुमान", "ऐप्स, वीडियो रिकॉर्डिंग, ऑफलाइन संगीत, फोटो और काम की फाइलें कितना स्थान लेंगी, पहले सोचें। ऑपरेटिंग सिस्टम भी स्टोरेज का एक हिस्सा इस्तेमाल करता है।"),
  ("विस्तार का विकल्प", "कुछ फोन में माइक्रोSD कार्ड का विकल्प नहीं होता। बाहरी क्लाउड स्टोरेज भी स्थानीय इंस्टॉल की जाने वाली ऐप्स का सीधा विकल्प नहीं है।"),
  ("सही कीमत और मॉडल", "एक ही फोन के 128GB और 256GB मॉडल अलग SKU हो सकते हैं। खरीदते समय प्रोसेसर, RAM, नेटवर्क और विक्रेता की वास्तविक कीमत अलग-अलग जाँचें।")]),
 "5g-phone-india-checklist": ("भारत में 5G फोन की जाँच", [
  ("सही नेटवर्क मॉडल", "ग्लोबल और भारतीय संस्करण में समर्थित नेटवर्क बैंड अलग हो सकते हैं। सिर्फ 5G लोगो देखकर हर भारतीय सेवा पर संगतता का निष्कर्ष नहीं निकालें।"),
  ("ऑपरेटर की शर्तें", "वास्तविक 5G उपलब्धता स्थान, ऑपरेटर, प्लान, सिम, सॉफ़्टवेयर और समर्थित बैंड पर निर्भर करती है। नेटवर्क क्षमता और कवरेज दो अलग बातें हैं।"),
  ("स्रोत कैसे जाँचें", "निर्माता के भारतीय स्पेसिफिकेशन और मोबाइल ऑपरेटर की ताज़ा आधिकारिक जानकारी मिलाएं। फोन के पूरे मॉडल नंबर और जरूरी SA/NSA बैंड का मिलान करें।")]),
 "compare-phones-exact-variants": ("अलग वेरिएंट मिलाए बिना फोन की तुलना", [
  ("पहचान सबसे पहले", "मॉडल नाम के साथ सटीक भौतिक RAM, स्टोरेज, नेटवर्क और भारतीय क्षेत्रीय संस्करण लिखें। Pro, Plus, 4G या 5G प्रत्यय को हटाकर दो अलग फोन को एक न समझें।"),
  ("प्रमाण की गुणवत्ता", "दो फोनों की तुलना में कैमरा नमूने, बैटरी परीक्षण और गेमिंग नतीजे एक जैसी पद्धति वाले होने चाहिए। गायब डेटा को शून्य अंक या खराब प्रदर्शन नहीं मानना चाहिए।"),
  ("मूल्य और रैंकिंग", "Coupon World में मूल्य केवल बजट की पात्रता तय करता है; प्रदर्शन-अंक में मूल्य का भार शून्य है। पुराने भाव को आज की बिक्री कीमत बताना गलत होगा।")]),
 "phone-price-stock-verification": ("फोन का मूल्य और स्टॉक कैसे जाँचें", [
  ("पुरानी कीमत क्या बताती है", "रिसर्च में सुरक्षित पुरानी कीमत केवल यह संकेत दे सकती है कि कोई वेरिएंट पहले किस बजट के पास था। यह आज का ऑफर, स्टॉक, डिलीवरी या अंतिम देय राशि नहीं है।"),
  ("दुकान में जाँच", "Amazon, Flipkart या Croma पर एक ही RAM/स्टोरेज SKU मिलाएं। कार्ड छूट, कूपन, एक्सचेंज, टैक्स, शुल्क, वारंटी और डिलीवरी शर्तें अलग पढ़ें।"),
  ("भरोसेमंद खरीद निर्णय", "केवल प्रमाणित और समय-सीमा के भीतर आने वाले ऑफर को लाइव ऑफर कहा जा सकता है। Coupon World के स्रोत-सर्च लिंक किसी विशिष्ट उत्पाद के स्टॉक का प्रमाण नहीं हैं।")]),
 "phone-research-evidence-method": ("Coupon World का शोध और प्रमाण तरीका", [
  ("सूत्रों का अंतर", "निर्माता की आधिकारिक स्पेसिफिकेशन से घोषित फीचर जाँच सकते हैं। स्वतंत्र प्रयोगशाला से वास्तविक बैटरी रनटाइम, कैमरा और गेमिंग परिणाम आते हैं। दोनों तरह के प्रमाण को एक समझना सही नहीं है।"),
  ("तिथि और परीक्षण", "रिसर्च रिकॉर्ड की जाँच की तिथि, पुराने रिटेलर मूल्य की तिथि और स्वतंत्र परीक्षण की तिथि अलग होती हैं। पुराने डेटा को केवल साइट के हालिया निर्माण के कारण नया न बताएं।"),
  ("ईमानदार सीमा", "किसी मॉडल के स्रोत से जुड़े फ़ील्ड होने का मतलब सभी भारतीय RAM/स्टोरेज वेरिएंट, मूल्य और स्टॉक की पुष्टि नहीं है। अनिश्चित सूचना को अनिश्चित ही दिखाया जाता है।")]),
 "camera-megapixels-vs-quality": ("मेगापिक्सल और कैमरा की असली गुणवत्ता", [
  ("बड़े आँकड़े की सीमा", "मेगापिक्सल छवि के पिक्सल की संख्या बताता है; सेंसर आकार, लेंस, कंप्यूटेशनल प्रोसेसिंग, गतिशील रेंज और शोर नियंत्रण अन्य निर्णायक कारक हैं।"),
  ("सही नमूना तुलना", "एक जैसे दृश्य, रोशनी और फोकस पर मुख्य, अल्ट्रावाइड और वीडियो कैमरों का आकलन करें। सोशल मीडिया पर संपीड़ित तस्वीर को निर्णायक मूल-गुणवत्ता परीक्षण न मानें।"),
  ("साक्ष्य की पारदर्शिता", "जहाँ तटस्थ कैमरा नमूने या विधिसम्मत स्कोर नहीं हैं, केवल 50MP या 200MP के आधार पर Top-3 घोषित नहीं किए जा सकते।")]),
 "battery-mah-vs-real-runtime": ("mAh और वास्तविक बैटरी चलने का समय", [
  ("ऊर्जा बनाम खपत", "mAh क्षमता का संकेत है, फोन कितने घंटे चलेगा यह स्क्रीन, प्रोसेसर, सिग्नल, ऐप्स और तापमान से भी तय होता है। एक बड़ी बैटरी वाले फोन का रनटाइम कभी छोटे बैटरी वाले फोन से कम हो सकता है।"),
  ("परीक्षण-पद्धति", "समान ब्राइटनेस, वाई-फाई/मोबाइल डेटा, स्क्रीन रिफ्रेश रेट और उपयोग-काम के परीक्षण अधिक उपयोगी हैं। केवल निर्माता के आदर्श परिस्थितियों वाले दावे को वास्तविक परीक्षण न लिखें।"),
  ("अतिरिक्त पहलू", "फास्ट चार्जिंग, बैटरी की उम्र और लंबे समय के उपयोग को क्षमता से अलग देखें। अनिश्चित रनटाइम पर रैंक नहीं बनाएं।")]),
 "phone-charging-watts-vs-time": ("चार्जिंग वॉट और पूरा समय", [
  ("वॉट किस बात का आँकड़ा है", "निर्माता का अधिकतम चार्जिंग वॉट पूरे चार्जिंग चक्र में स्थिर रहने वाली गति नहीं है। जैसे-जैसे बैटरी भरती है, सुरक्षा और तापमान के कारण गति बदल सकती है।"),
  ("समय किस तरह जाँचें", "0–50%, 0–80% और 0–100% के अलग परीक्षण में फर्क होता है। वास्तविक परीक्षण, फोन के सॉफ़्टवेयर, तापमान, केबल और चार्जर की जानकारी के साथ पढ़ें।"),
  ("बॉक्स का सामान", "चार्जर बॉक्स में मिलता है या नहीं, यह भारत के सटीक संस्करण के लिए देखें। सिर्फ अधिक W लिखे होने से तेज, सुरक्षित या हर चार्जर के साथ समान चार्जिंग साबित नहीं होती।")]),
}

SPEC_LABELS = {
 "chipset": "चिपसेट", "gpu": "ग्राफ़िक्स प्रोसेसर", "display_type": "स्क्रीन का प्रकार",
 "display_inches": "स्क्रीन का आकार", "display_resolution": "स्क्रीन रेजोल्यूशन",
 "display_refresh_max_hz": "अधिकतम रिफ्रेश रेट", "battery_mah_typical": "सामान्य बैटरी क्षमता",
 "battery_mah": "बैटरी क्षमता", "charging_wired_w": "वायर्ड चार्जिंग",
 "rear_main_mp": "मुख्य रियर कैमरा", "front_camera_mp": "फ्रंट कैमरा",
 "network_support": "नेटवर्क समर्थन", "security_update_policy": "सुरक्षा अपडेट नीति",
 "os_update_policy": "OS अपडेट नीति", "ram_gb": "भौतिक RAM", "storage_gb": "स्टोरेज",
 "ip_rating": "IP सुरक्षा रेटिंग", "bluetooth": "ब्लूटूथ", "weight_g": "वज़न",
 "nfc": "NFC समर्थन", "wifi": "वाई-फाई", "ois": "ऑप्टिकल इमेज स्थिरीकरण"
}

def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)

def doc(title: str, desc: str, path: str, en_path: str, main: str,
        *, indexed: bool = True, schema_type: str = "WebPage") -> str:
    canonical = SITE + path
    en_url = SITE + en_path
    graph = {"@context": "https://schema.org", "@type": schema_type,
             "name": title, "description": desc, "url": canonical,
             "inLanguage": "hi-IN", "isPartOf": {"@type": "WebSite",
               "name": "Coupon World", "url": SITE + "/"}}
    robots = "index,follow,max-image-preview:large" if indexed else "noindex,follow"
    jsonld = json.dumps(graph, ensure_ascii=False).replace("<", "\\u003c")
    alts = (f'<link rel="alternate" hreflang="en-IN" href="{esc(en_url)}">'
            f'<link rel="alternate" hreflang="hi-IN" href="{esc(canonical)}">') if en_path else ""
    return f'''<!doctype html><html lang="hi-IN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Coupon World</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{esc(canonical)}">{alts}
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<link rel="stylesheet" href="/assets/phone-guides.css?v=20261104">
<script type="application/ld+json">{jsonld}</script></head>
<body><a class="skip" href="#main">मुख्य सामग्री पर जाएँ</a>
<header><nav aria-label="मुख्य नेविगेशन"><a class="brand" href="/">Coupon World</a>
<a href="{HUB}">मोबाइल गाइड</a><a href="{PHONE_HUB}">फोन स्पेसिफिकेशन</a>
<a href="{BUDGET_HUB}">बजट</a>{f'<a hreflang="en" href="{esc(en_path)}">English</a>' if en_path else ""}</nav></header>
<main id="main"><p class="crumbs"><a href="/">होम</a> / <a href="{HUB}">हिंदी गाइड</a></p>
{main}</main><footer><a href="{HUB}">सभी हिंदी गाइड</a> · <a href="/guides/phone-budget-guides/">English guides</a>
<p>यह शोध-आधारित जानकारी है, स्वयं फोन इस्तेमाल करके किया गया परीक्षण नहीं।
पुराने मूल्य का अर्थ आज की कीमत या स्टॉक की पुष्टि नहीं है।
कुछ विक्रेता खोज लिंक संबद्ध (affiliate) हो सकते हैं; योग्य खरीद पर हमें कमीशन मिल सकता है।</p></footer></body></html>'''

def save(destination: Path, route: str, text: str) -> None:
    path = destination / route.lstrip("/")
    if route.endswith("/"):
        path = path / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def append_sitemap(destination: Path, urls: list[str], updated: str) -> None:
    target = destination / "sitemap.xml"
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    tree = ET.parse(target)
    root = tree.getroot()
    existing = {e.text for e in root.findall(f"{{{ns}}}url/{{{ns}}}loc")}
    for route in urls:
        url = SITE + route
        if url in existing:
            raise RuntimeError(f"Duplicate Hindi sitemap URL: {url}")
        entry = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(entry, f"{{{ns}}}loc").text = url
        ET.SubElement(entry, f"{{{ns}}}lastmod").text = updated
        existing.add(url)
    tree.write(target, encoding="utf-8", xml_declaration=True)

def build(destination: Path) -> dict:
    guides = json.loads((ROOT / "data/phone-guides.json").read_text(encoding="utf-8"))
    source_pages = guides["pages"]
    if len(source_pages) != 20 or {p["slug"] for p in source_pages} != set(GUIDE_COPY):
        raise RuntimeError("Hindi mirror requires an exact 20-guide English editorial match")
    catalog = json.loads((destination / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
    cards = {c["model_key"]: c for c in catalog.get("model_cards", [])}
    selected = [cards[k] for k in EDITORIAL_MODEL_KEYS if k in cards and eligible(cards[k])]
    if len(cards) != 232 or len(selected) != 50:
        raise RuntimeError("Hindi source mirror requires exactly 50 approved research pages")
    routes = []

    guide_cards = []
    for p in source_pages:
        slug = p["slug"]
        heading, sections = GUIDE_COPY[slug]
        route = "/hi/seo/" + slug + ".html"
        english = "/seo/" + slug + ".html"
        sections_html = "".join(
            f'<section><h2>{esc(h)}</h2><p>{esc(paragraph)}</p></section>'
            for h, paragraph in sections)
        check = f'<p><a href="/?{esc(urlencode({"q": p["query"]}))}#mobileResearchSearch">मौजूदा मोबाइल रिसर्च टूल में खोजें</a></p>'
        body = (f'<article><div class="eyebrow">भारत के मोबाइल खरीदारों के लिए</div>'
                f'<h1>{esc(heading)}</h1><p class="lead">{esc(heading)}: सटीक मॉडल, विश्वसनीय प्रमाण और खरीद से पहले की जाँच।</p>'
                f'<p class="byline">Coupon World संपादकीय शोध · मूल अंग्रेज़ी रिकॉर्ड: {esc(guides["updated"])}</p>'
                f'<aside class="note"><strong>महत्वपूर्ण सीमा:</strong><p>यह उपयोगी खरीद मार्गदर्शिका है,'
                ' लाइव कीमत का दावा, स्वतंत्र प्रयोगशाला परीक्षण या प्रमाणित Top-3 रैंकिंग नहीं।</p></aside>'
                + sections_html +
                '<section><h2>खरीद से पहले तीन चरण</h2><p>पहले मॉडल और भौतिक RAM/स्टोरेज पहचानें; '
                'फिर निर्माता का मूल दस्तावेज़ और उपलब्ध स्वतंत्र परीक्षण देखें; अंत में खुद विक्रेता पर '
                'वास्तविक कीमत, स्टॉक, शर्तें और वारंटी जाँचें।</p>' + check +
                '<p><a href="/hi/phones/">मूल निर्माता स्रोतों वाले फोन देखें</a> · '
                '<a href="/hi/budgets/">बजट और प्रमाणित रैंकिंग की स्थिति</a></p></section></article>')
        save(destination, route, doc(heading, f"{heading} — सटीक वेरिएंट और प्रमाण की जाँच के साथ हिंदी खरीद गाइड।",
                                     route, english, body, schema_type="Article"))
        routes.append(route)
        guide_cards.append(f'<a class="guide-card" href="{route}"><h3>{esc(heading)}</h3>'
                           '<p>साक्ष्य, तुलना और खरीद से पहले जाँच</p><span>हिंदी में पढ़ें →</span></a>')

    hub_main = ('<div class="eyebrow">COUPON WORLD / हिंदी रिसर्च</div>'
                '<h1>मोबाइल खरीदने की 20 हिंदी गाइड</h1>'
                '<p class="lead">अंग्रेज़ी में प्रकाशित उन्हीं 20 शोध विषयों को हिंदी में समझें। '
                'किसी पेज पर बिना प्रमाण के कीमत, टेस्ट स्कोर या सर्वश्रेष्ठ फोन घोषित नहीं किया जाता।</p>'
                '<p><a href="/hi/budgets/">₹10,000 से ₹1 लाख तक बजट चुनें</a> · '
                '<a href="/hi/phones/">50 निर्माता-स्रोत आधारित फोन पेज</a></p>'
                '<div class="guide-grid">' + "".join(guide_cards) + '</div>')
    save(destination, HUB, doc("हिंदी मोबाइल खरीद गाइड",
        "भारत में फोन चुनने के लिए 20 प्रमाण-आधारित हिंदी मार्गदर्शिकाएँ।",
        HUB, "/guides/phone-budget-guides/", hub_main, schema_type="CollectionPage"))
    routes.append(HUB)

    phone_cards = []
    for card in sorted(selected, key=lambda c: model_title(c).casefold()):
        model = model_title(card)
        slug = slug_for(card)
        route = PHONE_HUB + slug + "/"
        eng = "/phones/" + slug + "/"
        rows = []
        specs = accepted_specs(card)
        for key, item in specs:
            label = SPEC_LABELS.get(key, str(item.get("label") or key.replace("_", " ")))
            value = item.get("value")
            if isinstance(value, (list, tuple)):
                value = ", ".join(map(str, value))
            elif isinstance(value, bool):
                value = "हाँ" if value else "नहीं"
            checked = item.get("checked_at") or item.get("checked_date") or ""
            source = str(item["source_url"])
            rows.append(f'<tr><th scope="row">{esc(label)}</th><td>{esc(value)}</td>'
                        f'<td><a href="{esc(source)}" rel="noopener noreferrer" target="_blank">मूल निर्माता स्रोत</a>'
                        f' {esc(checked)}</td></tr>')
        missing = card.get("missing_specifications") or []
        missing_text = ", ".join(SPEC_LABELS.get(k, str(k).replace("_", " ")) for k in missing[:8])
        retailer_search = []
        for item in card.get("retailer_search_links") or []:
            u = str(item.get("url") or "")
            if not u.startswith(("https://www.amazon.in/", "https://www.flipkart.com/", "https://www.croma.com/")):
                continue
            retailer_search.append(f'<a href="{esc(u)}" rel="sponsored nofollow noopener noreferrer" target="_blank">'
                                   f'{esc(item.get("retailer") or "विक्रेता")} पर खोज</a>')
        main = (f'<article><div class="eyebrow">स्रोत-सहित तकनीकी जानकारी / भारत</div>'
                f'<h1>{esc(model)} के स्पेसिफिकेशन</h1>'
                f'<p class="lead">{esc(model)} के {len(specs)} स्रोत-जुड़े तकनीकी विवरण, '
                'अपूर्ण जानकारी और खरीदने से पहले सटीक वेरिएंट की जाँच।</p>'
                '<aside class="note"><strong>यह शोध है, खरीद की रैंकिंग नहीं।</strong>'
                '<p>निर्माता का मॉडल-स्तरीय स्रोत हर भारतीय RAM/स्टोरेज विकल्प की पहचान,'
                ' वास्तविक कैमरा गुणवत्ता, बैटरी रनटाइम, गेमिंग FPS, कीमत या स्टॉक प्रमाणित नहीं करता।</p></aside>'
                f'<p class="byline">स्रोतों की रिसर्च जाँच: {esc(card.get("research_checked_at") or "तिथि उपलब्ध नहीं")}</p>'
                '<section><h2>निर्माता से दर्ज स्पेसिफिकेशन</h2>'
                '<div class="mobile-fact-table-wrap"><table class="mobile-fact-table">'
                '<thead><tr><th>तकनीकी जानकारी</th><th>दर्ज मान</th><th>प्रमाण</th></tr></thead>'
                '<tbody>' + "".join(rows) + '</tbody></table></div>'
                '<p>तकनीकी मानों को स्रोत जैसा दर्ज किया गया है; अंग्रेज़ी में दिए गए मॉडल और फीचर नाम'
                ' पहचान की सटीकता के लिए रखे गए हैं।</p></section>'
                '<section><h2>अपूर्ण जानकारी और सावधानियाँ</h2>'
                f'<p>{esc(missing_text) if missing_text else "नए फ़ील्ड की अनुपस्थिति से सम्पूर्ण सत्यापन सिद्ध नहीं होता।"}</p>'
                '<p>पुराने रिटेलर मूल्य केवल बजट की प्रारंभिक जाँच में सहायक हो सकते हैं। '
                'प्रदर्शन स्कोर में मूल्य का भार शून्य है। किसी भी पुराने भाव को वर्तमान ऑफर न मानें।</p>'
                '<p>खरीदने से पहले भौतिक RAM, स्टोरेज, भारत का मॉडल नंबर, वारंटी, विक्रेता और '
                'डिलीवरी की स्वतंत्र पुष्टि करें।</p></section>'
                '<section><h2>इस मॉडल की तुलना करें</h2>'
                f'<p><a href="/?{esc(urlencode({"q": model}))}#mobileResearchSearch">रिसर्च टूल में {esc(model)} खोजें</a></p>'
                '<p>कैमरा, बैटरी और गेमिंग का विजेता स्वतंत्र, तुलनीय परीक्षण के बिना घोषित नहीं है।</p></section>'
                '<section><h2>विक्रेता खोज (सत्यापित ऑफर नहीं)</h2>'
                '<p>ये खोज लिंक हैं, इस विशेष वेरिएंट की वर्तमान उपलब्धता के प्रमाण नहीं।</p>'
                '<p>' + (" · ".join(retailer_search) if retailer_search else "इस रिकॉर्ड में सत्यापित विक्रेता लिंक नहीं है।") + '</p></section>'
                '<section><h2>प्रमाण की पद्धति</h2><p><a href="/hi/seo/phone-research-evidence-method.html">'
                'हम डेटा की विश्वसनीयता कैसे आँकते हैं</a>। इस पेज पर स्वयं डिवाइस टेस्ट करने का दावा नहीं है।</p></section></article>')
        save(destination, route, doc(f"{model} के स्पेसिफिकेशन",
             f"{model} — निर्माता स्रोतों वाले {len(specs)} तकनीकी विवरण और अपूर्ण जानकारी हिंदी में।",
             route, eng, main))
        routes.append(route)
        phone_cards.append(f'<a class="guide-card" href="{route}"><h3>{esc(model)}</h3>'
                           f'<p>{len(specs)} तकनीकी फ़ील्ड · {esc(card.get("status"))}</p>'
                           '<span>विवरण देखें →</span></a>')
    phone_main = ('<h1>50 स्मार्टफोन के स्रोत-सहित स्पेसिफिकेशन</h1>'
                  '<p class="lead">उन्हीं 50 संपादकीय स्वीकृत मॉडलों के तकनीकी तथ्य हिंदी में, '
                  'मूल निर्माता लिंक और अनिश्चित जानकारी के साथ। केवल स्रोत होने से वास्तविक प्रदर्शन विजेता प्रमाणित नहीं होता।</p>'
                  '<div class="guide-grid">' + "".join(phone_cards) + '</div>')
    save(destination, PHONE_HUB, doc("हिंदी स्मार्टफोन स्पेसिफिकेशन", "भारत के 50 शोधित फोन: निर्माता स्रोत और सटीक विवरण।",
         PHONE_HUB, "/phones/", phone_main, schema_type="CollectionPage"))
    routes.append(PHONE_HUB)

    # Budget bands have no certified category Top-3. Show the requested three
    # categories with explicit evidence pending, without fabricated ranking.
    budget_cards = []
    for budget in BUDGETS:
        route = f"/hi/budgets/{budget}/"
        start = max(0, budget - 5000)
        category = []
        for name, caveat in [
            ("कैमरा", "समान पद्धति वाले वास्तविक फोटो और वीडियो परीक्षण"),
            ("बैटरी", "तुलनीय सक्रिय-उपयोग रनटाइम परीक्षण"),
            ("गेमिंग", "लंबे समय के FPS, ताप और स्थिरता के परीक्षण"),
        ]:
            category.append(f'<section><h2>सर्वश्रेष्ठ {esc(name)} फोन — अधिकतम 3</h2>'
                            f'<p>वर्तमान स्थिति: प्रमाणित Top-3 उपलब्ध नहीं। इस श्रेणी के लिए '
                            f'{esc(caveat)}, सटीक भारत वेरिएंट और दिनांकित बजट प्रमाण '
                            'आवश्यक हैं। अनुमान से 1, 2, 3 रैंक नहीं दी जाती।</p></section>')
        main = (f'<article><h1>₹{budget:,} तक के फोन: कैमरा, बैटरी और गेमिंग</h1>'
                '<p class="lead">सही बजट और सटीक RAM/स्टोरेज मॉडल चुनने के लिए '
                'मौजूदा रिसर्च का उपयोग करें। हर विषय में अधिकतम तीन सत्यापित परिणाम ही दिए जाएँगे।</p>'
                f'<p>यह शॉर्टकट ₹{start:,} से ₹{budget:,} से कम के पुराने '
                'कीमत-संदर्भ बैंड से तुलना करता है; यह आज की खुदरा कीमत नहीं है। '
                'कम बजट भी खोज में शामिल करना हो तो अपनी सीमा स्पष्ट लिखें।</p>'
                '<aside class="note"><strong>रैंकिंग की गुणवत्ता पहली शर्त है।</strong>'
                '<p>वर्तमान प्रकाशन में प्रमाणित कैटेगरी Top-3 सूची उपलब्ध नहीं है। '
                'पुराना मूल्य केवल बजट पात्रता के लिए इस्तेमाल होगा, रैंकिंग स्कोर में इसका भार 0% है। '
                'यह पेज सूची प्रमाणित होने तक Google अनुक्रमण से बाहर है।</p></aside>'
                + "".join(category) +
                f'<section><h2>इस बजट में मॉडल खोजें</h2>'
                f'<p><a href="/?{urlencode({"q": f"phone under {budget}"})}#mobileResearchSearch">'
                'मौजूदा मोबाइल रिसर्च खोलें</a>। पहले सटीक भारत वेरिएंट, फिर निर्माता के तथ्य, '
                'तुलनीय स्वतंत्र परीक्षण और अंत में विक्रेता की वर्तमान कीमत जाँचें।</p></section></article>')
        save(destination, route, doc(f"₹{budget:,} तक के मोबाइल — कैमरा, बैटरी, गेमिंग",
             f"₹{budget:,} बजट के लिए कैमरा, बैटरी और गेमिंग की प्रमाणित Top-3 स्थिति।",
             route, "", main, indexed=False))
        budget_cards.append(f'<a class="guide-card" href="{route}"><h3>₹{budget:,} तक</h3>'
                            '<p>कैमरा · बैटरी · गेमिंग · प्रमाण की स्थिति</p>'
                            '<span>बजट देखें →</span></a>')
    budget_main = ('<h1>₹10,000 से ₹1 लाख: हर ₹5,000 का मोबाइल बजट</h1>'
                   '<p class="lead">19 बजट विकल्प। हर रेंज में कैमरा, बैटरी और गेमिंग के लिए अधिकतम '
                   'तीन प्रमाण-आधारित फोन दिखाने का मानक है। पर्याप्त जाँचे हुए परिणाम न होने पर '
                   'नाम और रैंकिंग नहीं गढ़ी जाती।</p>'
                   '<p>वर्तमान स्थिति में बजट विकल्प शोध-मार्गदर्शन हैं, आज की कीमतों या Top-3 की '
                   'पुष्टि नहीं। कीमत प्रदर्शन स्कोर का भाग नहीं है।</p>'
                   '<div class="guide-grid">' + "".join(budget_cards) + '</div>')
    save(destination, BUDGET_HUB, doc("मोबाइल बजट गाइड हिंदी",
         "₹10,000 से ₹1 लाख तक 19 मोबाइल बजट विकल्प और कैमरा, बैटरी तथा गेमिंग की प्रमाण स्थिति।",
         BUDGET_HUB, "", budget_main, schema_type="CollectionPage"))
    routes.append(BUDGET_HUB)
    if len(routes) != 73: # 20 guides + guide hub + 50 models + phone hub + budget hub 
        raise RuntimeError(f"Unexpected Hindi indexable route count: {len(routes)}")
    append_sitemap(destination, routes, guides["updated"])
    return {"guide_pages": 20, "phone_pages": 50, "budget_pages": len(BUDGETS),
            "hubs": 3, "indexable_routes": len(routes)}

if __name__ == "__main__":
    raise SystemExit("This module is invoked by scripts/build_public_pages.py")
