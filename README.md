[index.html](https://github.com/user-attachments/files/29097473/index.html)
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
<title>CouponWorld Noida - Latest Coupons & Promo Codes for Noida</title>
<meta name="description" content="Latest verified coupons, promo codes and discount offers in Noida for Zomato, Swiggy, Amazon, Flipkart, Domino's, Blinkit, Urban Company, Myntra, Zepto and Livpure.">
<meta name="robots" content="index, follow">

<!--
  =====================================================================
  HOW TO EDIT THIS FILE (for someone with NO coding experience)
  =====================================================================
  1. Open this file in Notepad (Windows) or any text editor.
  2. Scroll down to the section that says:
         ===== COUPON DATA (EDIT THIS PART ONLY) =====
  3. Each coupon is one block between { and }. To change a coupon:
       - Change the text inside the quotes " "
       - Do NOT remove commas , or quote marks " "
       - Do NOT remove the { or }
  4. To add a new coupon: copy one whole block (from { to },) and paste
     it just above the closing ]; line, then edit the text inside it.
  5. To remove a coupon: delete its whole block (from { to its closing },)
  6. Save the file. Re-open index.html in any browser to check it looks right.
  7. Upload the same file to your hosting (Cloudflare Pages) to go live.
  =====================================================================
-->

<style>
  :root{
    --blue:#1a56db;
    --blue-dark:#1543a8;
    --orange:#f97316;
    --bg:#ffffff;
    --text:#1f2330;
    --muted:#6b7280;
    --border:#e5e7eb;
    --green:#15803d;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;}
  body{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    background:var(--bg);
    color:var(--text);
    line-height:1.5;
    -webkit-text-size-adjust:100%;
  }
  img{max-width:100%;display:block;}
  a{color:inherit;text-decoration:none;}

  /* ===== HEADER ===== */
  header.site-header{
    background:var(--blue);
    color:#fff;
    padding:14px 16px;
    position:sticky;
    top:0;
    z-index:50;
    box-shadow:0 1px 4px rgba(0,0,0,.12);
  }
  .header-inner{
    max-width:900px;
    margin:0 auto;
    display:flex;
    align-items:center;
    justify-content:space-between;
  }
  .brand-logo{
    font-size:20px;
    font-weight:800;
    letter-spacing:.2px;
  }
  .brand-logo span{color:var(--orange);}
  .header-tag{
    font-size:11px;
    font-weight:600;
    background:rgba(255,255,255,.18);
    padding:4px 9px;
    border-radius:999px;
    white-space:nowrap;
  }
  .header-sub{
    max-width:900px;
    margin:6px auto 0;
    font-size:12.5px;
    color:rgba(255,255,255,.85);
  }

  /* ===== MAIN / COUPON GRID ===== */
  main{
    max-width:900px;
    margin:0 auto;
    padding:18px 14px 28px;
  }
  .page-title{
    font-size:19px;
    font-weight:700;
    margin:4px 0 2px;
  }
  .page-sub{
    font-size:13px;
    color:var(--muted);
    margin:0 0 16px;
  }
  .coupon-grid{
    display:grid;
    grid-template-columns:1fr;
    gap:14px;
  }
  @media(min-width:640px){
    .coupon-grid{grid-template-columns:1fr 1fr;}
  }

  .coupon-card{
    border:1px solid var(--border);
    border-radius:14px;
    padding:14px;
    background:#fff;
    box-shadow:0 1px 2px rgba(0,0,0,.04);
    display:flex;
    flex-direction:column;
    gap:8px;
  }
  .coupon-top{
    display:flex;
    align-items:center;
    gap:10px;
  }
  .coupon-logo{
    width:42px;
    height:42px;
    border-radius:10px;
    background:#f1f4f9;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:800;
    font-size:14px;
    color:var(--blue-dark);
    flex-shrink:0;
  }
  .coupon-brand{
    font-weight:700;
    font-size:15px;
  }
  .coupon-cat{
    font-size:11px;
    color:var(--muted);
  }
  .coupon-offer{
    font-size:15px;
    font-weight:600;
    color:var(--text);
    margin-top:2px;
  }
  .coupon-desc{
    font-size:12.5px;
    color:var(--muted);
  }
  .coupon-meta{
    display:flex;
    flex-wrap:wrap;
    gap:8px;
    font-size:11px;
    color:var(--muted);
    margin-top:2px;
  }
  .meta-pill{
    background:#f3f4f6;
    padding:3px 8px;
    border-radius:999px;
  }
  .meta-pill.verified{
    background:#ecfdf5;
    color:var(--green);
  }

  .code-row{
    display:flex;
    align-items:center;
    border:1.5px dashed var(--orange);
    border-radius:10px;
    overflow:hidden;
    margin-top:4px;
  }
  .code-text{
    flex:1;
    padding:9px 10px;
    font-weight:700;
    font-size:14px;
    letter-spacing:.5px;
    color:var(--blue-dark);
    background:#fff7ed;
    overflow-x:auto;
    white-space:nowrap;
  }
  .copy-btn{
    border:none;
    background:var(--orange);
    color:#fff;
    font-weight:700;
    font-size:13px;
    padding:9px 14px;
    cursor:pointer;
    flex-shrink:0;
  }
  .copy-btn:active{background:#ea670e;}

  .visit-btn{
    display:block;
    text-align:center;
    margin-top:2px;
    padding:9px 12px;
    border-radius:10px;
    background:var(--blue);
    color:#fff;
    font-weight:600;
    font-size:13.5px;
  }
  .visit-btn:active{background:var(--blue-dark);}

  .copied-msg{
    font-size:11.5px;
    color:var(--green);
    font-weight:600;
    display:none;
    text-align:center;
  }

  /* ===== FOOTER ===== */
  footer.site-footer{
    background:#f9fafb;
    border-top:1px solid var(--border);
    padding:18px 16px 90px;
    text-align:center;
    font-size:12px;
    color:var(--muted);
  }
  footer.site-footer p{margin:4px 0;}
  .disclaimer{
    max-width:700px;
    margin:0 auto;
    font-size:11.5px;
    line-height:1.6;
  }

  /* WhatsApp floating button */
  .wa-float{
    position:fixed;
    bottom:18px;
    right:18px;
    background:#25D366;
    width:54px;
    height:54px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    box-shadow:0 3px 10px rgba(0,0,0,.25);
    z-index:60;
  }
  .wa-float svg{width:28px;height:28px;}

  .last-updated-banner{
    max-width:900px;
    margin:10px auto 0;
    background:#eff6ff;
    border:1px solid #dbeafe;
    color:var(--blue-dark);
    font-size:12px;
    font-weight:600;
    padding:8px 14px;
    border-radius:10px;
    text-align:center;
  }
</style>
</head>
<body>

<!-- ================= HEADER (Section 1) ================= -->
<header class="site-header">
  <div class="header-inner">
    <div class="brand-logo">Coupon<span>World</span></div>
    <div class="header-tag">📍 Noida</div>
  </div>
  <div class="header-sub">Latest coupons & promo codes for Noida — updated by hand, not by bots.</div>
</header>

<main>
  <h1 class="page-title">Today's Coupons in Noida</h1>
  <p class="page-sub">Tap "Copy Code", then tap "Visit Store" to use it. If a code stops working, please tell us on WhatsApp (button bottom-right).</p>

  <!--
    EDITOR NOTE: This blue box shows the date the WHOLE PAGE was last
    checked. Just type today's date here in plain words when you check
    all coupons, e.g. "17 June 2026".
  -->
  <div class="last-updated-banner" id="page-updated-banner">
    Page last checked on: <span id="page-updated-date">17 June 2026</span>
  </div>

  <div class="coupon-grid" id="coupon-grid"></div>
</main>

<!-- ================= FOOTER (Section 3) ================= -->
<footer class="site-footer">
  <p><strong>CouponWorld Noida</strong></p>
  <p class="disclaimer">
    We are not affiliated with the brands listed above. Logos and brand names belong to their
    respective owners and are used only to identify the offer. Discounts, codes and terms can
    change anytime at the brand's discretion — always confirm the final price on the brand's
    own app or website before paying. Please use the WhatsApp button to report an expired code.
  </p>
  <p>© <span id="year"></span> CouponWorld.in</p>
</footer>

<!-- WhatsApp floating contact button -->
<a class="wa-float" id="wa-float-btn" href="#" target="_blank" rel="noopener" aria-label="Contact us on WhatsApp">
  <svg viewBox="0 0 32 32" fill="#fff" xmlns="http://www.w3.org/2000/svg">
    <path d="M16.04 3C9.37 3 3.96 8.4 3.96 15.06c0 2.41.68 4.66 1.86 6.57L4 29l7.6-1.99a12.07 12.07 0 0 0 4.44.85h.01c6.67 0 12.08-5.4 12.08-12.06C28.13 8.4 22.72 3 16.04 3zm0 21.86h-.01a10.1 10.1 0 0 1-5.15-1.4l-.37-.22-4.51 1.18 1.2-4.4-.24-.38a10.05 10.05 0 0 1-1.55-5.38c0-5.56 4.53-10.08 10.1-10.08 2.7 0 5.23 1.05 7.14 2.95a10.02 10.02 0 0 1 2.96 7.13c0 5.56-4.54 10.08-10.1 10.08zm5.53-7.55c-.3-.15-1.78-.88-2.06-.98-.28-.1-.48-.15-.68.15-.2.3-.78.98-.96 1.18-.18.2-.35.22-.65.07-1.77-.88-2.93-1.57-4.1-3.57-.31-.53.31-.49.89-1.64.1-.2.05-.37-.05-.52-.1-.15-.66-1.6-.9-2.18-.24-.58-.49-.5-.68-.5-.18 0-.4-.02-.6-.02-.2 0-.53.07-.8.37-.28.3-1.06 1.04-1.06 2.54s1.1 2.95 1.25 3.15c.15.2 2.1 3.2 5.08 4.36 2.98 1.16 2.98.77 3.52.72.54-.05 1.78-.73 2.03-1.43.25-.7.25-1.3.18-1.43-.07-.13-.27-.2-.57-.35z"/>
  </svg>
</a>

<script>
  document.getElementById('year').textContent = new Date().getFullYear();

  /* =====================================================================
     ===== COUPON DATA (EDIT THIS PART ONLY) =====
     =====================================================================
     Each coupon below is one { ... } block. Fields explained:

       brand        -> Brand name shown on the card (e.g. "Zomato")
       logoText     -> Short text shown inside the little logo box
                       (e.g. "Z" or "AMZ"). Keep it 1-4 letters.
       category     -> Small grey text under brand name (e.g. "Food Delivery")
       offer        -> The big bold offer line (e.g. "Flat 50% OFF up to ₹150")
       desc         -> One short line with extra detail / conditions
       code         -> The actual coupon code text (e.g. "NOIDA50")
                       If there is no code (just a link deal), write "NO CODE NEEDED"
       minOrder     -> Small text like "Min order ₹199" or "" if none
       expiry       -> Text like "Valid till 30 Jun 2026" or "No expiry given"
       verified     -> Date you personally checked this coupon, e.g. "15 Jun 2026"
       link         -> Where "Visit Store" button goes (brand website/app link)

     TO ADD A COUPON: copy one full block from { to }, paste above the
     closing  ];  line below, then change the text inside the quotes.

     TO REMOVE A COUPON: delete its whole block, including the comma
     after its closing }.
     ===================================================================== */

  const coupons = [
    {
      brand: "Zomato",
      logoText: "Z",
      category: "Food Delivery",
      offer: "Flat 50% OFF up to ₹150",
      desc: "On orders from select Noida restaurants via Zomato app.",
      code: "ZOMNOIDA50",
      minOrder: "Min order ₹199",
      expiry: "Valid till 30 Jun 2026",
      verified: "15 Jun 2026",
      link: "https://www.zomato.com/noida"
    },
    {
      brand: "Zomato",
      logoText: "Z",
      category: "Food Delivery",
      offer: "₹125 OFF on Zomato Gold orders",
      desc: "Applicable for Zomato Gold members ordering in Noida & Greater Noida.",
      code: "GOLD125",
      minOrder: "Min order ₹349",
      expiry: "Valid till 25 Jun 2026",
      verified: "15 Jun 2026",
      link: "https://www.zomato.com/noida"
    },
    {
      brand: "Zomato",
      logoText: "Z",
      category: "Food Delivery",
      offer: "Free Delivery on your first 3 orders",
      desc: "New users in Noida sector pin codes only.",
      code: "NO CODE NEEDED",
      minOrder: "Min order ₹99",
      expiry: "No expiry given",
      verified: "12 Jun 2026",
      link: "https://www.zomato.com/noida"
    },

    {
      brand: "Swiggy",
      logoText: "SW",
      category: "Food Delivery",
      offer: "Flat 60% OFF up to ₹120",
      desc: "On your first Swiggy order from this device.",
      code: "SWIGGYNEW",
      minOrder: "Min order ₹149",
      expiry: "Valid till 30 Jun 2026",
      verified: "15 Jun 2026",
      link: "https://www.swiggy.com/noida"
    },
    {
      brand: "Swiggy",
      logoText: "SW",
      category: "Food Delivery",
      offer: "20% OFF on Swiggy Instamart",
      desc: "Groceries & essentials delivered fast in Noida sectors.",
      code: "INSTA20",
      minOrder: "Min order ₹249",
      expiry: "Valid till 28 Jun 2026",
      verified: "14 Jun 2026",
      link: "https://www.swiggy.com/instamart"
    },
    {
      brand: "Swiggy",
      logoText: "SW",
      category: "Food Delivery",
      offer: "Buy 1 Get 1 on select restaurants",
      desc: "Check the offer tag inside the app for participating outlets.",
      code: "NO CODE NEEDED",
      minOrder: "",
      expiry: "Valid till 20 Jun 2026",
      verified: "13 Jun 2026",
      link: "https://www.swiggy.com/noida"
    },

    {
      brand: "Amazon",
      logoText: "A",
      category: "Shopping",
      offer: "Up to 80% OFF Electronics Sale",
      desc: "On select electronics, brand and category specific.",
      code: "NO CODE NEEDED",
      minOrder: "",
      expiry: "Check site for sale dates",
      verified: "15 Jun 2026",
      link: "https://www.amazon.in"
    },
    {
      brand: "Amazon",
      logoText: "A",
      category: "Shopping",
      offer: "10% Instant Discount on HDFC Cards",
      desc: "On eligible purchases paid via HDFC Bank credit/debit card.",
      code: "NO CODE NEEDED",
      minOrder: "Min order ₹3000",
      expiry: "Valid till 30 Jun 2026",
      verified: "10 Jun 2026",
      link: "https://www.amazon.in"
    },
    {
      brand: "Amazon",
      logoText: "A",
      category: "Shopping",
      offer: "Extra 10% OFF for Prime Members",
      desc: "On top of existing deal price for Prime members.",
      code: "PRIME10",
      minOrder: "",
      expiry: "No expiry given",
      verified: "11 Jun 2026",
      link: "https://www.amazon.in"
    },

    {
      brand: "Flipkart",
      logoText: "FK",
      category: "Shopping",
      offer: "Flat ₹500 OFF on Fashion",
      desc: "On apparel & footwear above the minimum order value.",
      code: "FASHION500",
      minOrder: "Min order ₹1999",
      expiry: "Valid till 26 Jun 2026",
      verified: "14 Jun 2026",
      link: "https://www.flipkart.com"
    },
    {
      brand: "Flipkart",
      logoText: "FK",
      category: "Shopping",
      offer: "5% Cashback via Flipkart Axis Card",
      desc: "Unlimited cashback for Flipkart Axis Bank credit card users.",
      code: "NO CODE NEEDED",
      minOrder: "",
      expiry: "No expiry given",
      verified: "9 Jun 2026",
      link: "https://www.flipkart.com"
    },
    {
      brand: "Flipkart",
      logoText: "FK",
      category: "Shopping",
      offer: "Big Saving Days - Up to 70% OFF",
      desc: "Seasonal sale across categories, check app for live dates.",
      code: "NO CODE NEEDED",
      minOrder: "",
      expiry: "Check site for sale dates",
      verified: "8 Jun 2026",
      link: "https://www.flipkart.com"
    },

    {
      brand: "Domino's",
      logoText: "DM",
      category: "Food Delivery",
      offer: "Buy 1 Get 1 Free on Medium Pizza",
      desc: "Valid on dine-in & delivery from Noida outlets.",
      code: "DOMS2FOR1",
      minOrder: "",
      expiry: "Valid till 22 Jun 2026",
      verified: "15 Jun 2026",
      link: "https://www.dominos.co.in"
    },
    {
      brand: "Domino's",
      logoText: "DM",
      category: "Food Delivery",
      offer: "30% OFF on orders above ₹500",
      desc: "Applicable on app & website orders in Noida sectors.",
      code: "DOM30",
      minOrder: "Min order ₹500",
      expiry: "Valid till 24 Jun 2026",
      verified: "13 Jun 2026",
      link: "https://www.dominos.co.in"
    },
    {
      brand: "Domino's",
      logoText: "DM",
      category: "Food Delivery",
      offer: "Free Garlic Breadsticks on orders above ₹399",
      desc: "Add to cart, discount applied automatically with code.",
      code: "FREEBREAD",
      minOrder: "Min order ₹399",
      expiry: "Valid till 18 Jun 2026",
      verified: "12 Jun 2026",
      link: "https://www.dominos.co.in"
    },

    {
      brand: "Blinkit",
      logoText: "BQ",
      category: "Grocery Delivery",
      offer: "Flat ₹75 OFF on first order",
      desc: "New users only, instant grocery delivery in Noida.",
      code: "BLINK75",
      minOrder: "Min order ₹199",
      expiry: "Valid till 30 Jun 2026",
      verified: "15 Jun 2026",
      link: "https://blinkit.com"
    },
    {
      brand: "Blinkit",
      logoText: "BQ",
      category: "Grocery Delivery",
      offer: "Free Delivery on all orders",
      desc: "No minimum order, applicable for select Noida pin codes.",
      code: "NO CODE NEEDED",
      minOrder: "",
      expiry: "No expiry given",
      verified: "11 Jun 2026",
      link: "https://blinkit.com"
    },
    {
      brand: "Blinkit",
      logoText: "BQ",
      category: "Grocery Delivery",
      offer: "Up to 40% OFF Fruits & Vegetables",
      desc: "Daily fresh deals, prices vary by item.",
      code: "NO CODE NEEDED",
      minOrder: "",
      expiry: "Check app for daily deals",
      verified: "15 Jun 2026",
      link: "https://blinkit.com"
    },

    {
      brand: "Urban Company",
      logoText: "UC",
      category: "Home Services",
      offer: "30% OFF on AC Service & Repair",
      desc: "Book a verified professional for AC servicing in Noida.",
      code: "UCAC30",
      minOrder: "",
      expiry: "Valid till 28 Jun 2026",
      verified: "14 Jun 2026",
      link: "https://www.urbancompany.com/noida"
    },
    {
      brand: "Urban Company",
      logoText: "UC",
      category: "Home Services",
      offer: "Flat ₹200 OFF on Salon at Home",
      desc: "For women's salon services booked in Noida sectors.",
      code: "UCSALON200",
      minOrder: "Min order ₹999",
      expiry: "Valid till 25 Jun 2026",
      verified: "13 Jun 2026",
      link: "https://www.urbancompany.com/noida"
    },
    {
      brand: "Urban Company",
      logoText: "UC",
      category: "Home Services",
      offer: "20% OFF on Deep Cleaning",
      desc: "Home/kitchen/bathroom deep cleaning packages.",
      code: "CLEAN20",
      minOrder: "",
      expiry: "Valid till 30 Jun 2026",
      verified: "10 Jun 2026",
      link: "https://www.urbancompany.com/noida"
    },

    {
      brand: "Myntra",
      logoText: "MY",
      category: "Fashion",
      offer: "Up to 80% OFF End of Season Sale",
      desc: "Across top fashion & lifestyle brands.",
      code: "NO CODE NEEDED",
      minOrder: "",
      expiry: "Check site for sale dates",
      verified: "15 Jun 2026",
      link: "https://www.myntra.com"
    },
    {
      brand: "Myntra",
      logoText: "MY",
      category: "Fashion",
      offer: "Extra 10% OFF for First Order",
      desc: "New user discount on top of best price shown.",
      code: "MYNTRA10",
      minOrder: "Min order ₹999",
      expiry: "No expiry given",
      verified: "9 Jun 2026",
      link: "https://www.myntra.com"
    },
    {
      brand: "Myntra",
      logoText: "MY",
      category: "Fashion",
      offer: "Flat 150 OFF on app orders",
      desc: "App-exclusive discount, applicable across categories.",
      code: "APP150",
      minOrder: "Min order ₹1000",
      expiry: "Valid till 20 Jun 2026",
      verified: "8 Jun 2026",
      link: "https://www.myntra.com"
    },

    {
      brand: "Zepto",
      logoText: "ZP",
      category: "Grocery Delivery",
      offer: "10 Min Delivery + Flat ₹60 OFF",
      desc: "On first order from Zepto in Noida sectors.",
      code: "ZEPTO60",
      minOrder: "Min order ₹149",
      expiry: "Valid till 30 Jun 2026",
      verified: "15 Jun 2026",
      link: "https://www.zeptonow.com"
    },
    {
      brand: "Zepto",
      logoText: "ZP",
      category: "Grocery Delivery",
      offer: "Free Delivery above ₹99",
      desc: "Standard free delivery threshold for Noida sectors.",
      code: "NO CODE NEEDED",
      minOrder: "Min order ₹99",
      expiry: "No expiry given",
      verified: "12 Jun 2026",
      link: "https://www.zeptonow.com"
    },
    {
      brand: "Zepto",
      logoText: "ZP",
      category: "Grocery Delivery",
      offer: "Up to 50% OFF Dairy & Bakery",
      desc: "Daily changing offers, check app for current items.",
      code: "NO CODE NEEDED",
      minOrder: "",
      expiry: "Check app for daily deals",
      verified: "15 Jun 2026",
      link: "https://www.zeptonow.com"
    },

    {
      brand: "Livpure",
      logoText: "LV",
      category: "Water Purifiers & Appliances",
      offer: "Flat ₹1000 OFF on RO Water Purifiers",
      desc: "On select Livpure RO models with installation.",
      code: "LIVPURE1000",
      minOrder: "",
      expiry: "Valid till 30 Jun 2026",
      verified: "14 Jun 2026",
      link: "https://www.livpure.com"
    },
    {
      brand: "Livpure",
      logoText: "LV",
      category: "Water Purifiers & Appliances",
      offer: "Free Annual Maintenance on Purchase",
      desc: "1-year free AMC bundled with new purifier purchase.",
      code: "NO CODE NEEDED",
      minOrder: "",
      expiry: "Valid till 25 Jun 2026",
      verified: "11 Jun 2026",
      link: "https://www.livpure.com"
    },
    {
      brand: "Livpure",
      logoText: "LV",
      category: "Water Purifiers & Appliances",
      offer: "EMI starting ₹499/month",
      desc: "No-cost EMI option on select RO purifier models.",
      code: "NO CODE NEEDED",
      minOrder: "",
      expiry: "No expiry given",
      verified: "10 Jun 2026",
      link: "https://www.livpure.com"
    }
  ];

  /* =====================================================================
     ===== END OF COUPON DATA — do not edit below this line =====
     ===================================================================== */

  function escapeHtml(str){
    return String(str)
      .replace(/&/g,"&amp;")
      .replace(/</g,"&lt;")
      .replace(/>/g,"&gt;");
  }

  function renderCoupons(){
    const grid = document.getElementById('coupon-grid');
    grid.innerHTML = '';

    coupons.forEach(function(c, idx){
      const card = document.createElement('div');
      card.className = 'coupon-card';

      const noCode = (c.code || '').trim().toUpperCase() === 'NO CODE NEEDED';

      card.innerHTML =
        '<div class="coupon-top">' +
          '<div class="coupon-logo">' + escapeHtml(c.logoText || '?') + '</div>' +
          '<div>' +
            '<div class="coupon-brand">' + escapeHtml(c.brand) + '</div>' +
            '<div class="coupon-cat">' + escapeHtml(c.category || '') + '</div>' +
          '</div>' +
        '</div>' +
        '<div class="coupon-offer">' + escapeHtml(c.offer) + '</div>' +
        (c.desc ? '<div class="coupon-desc">' + escapeHtml(c.desc) + '</div>' : '') +
        '<div class="coupon-meta">' +
          (c.minOrder ? '<span class="meta-pill">' + escapeHtml(c.minOrder) + '</span>' : '') +
          '<span class="meta-pill">' + escapeHtml(c.expiry || '') + '</span>' +
          '<span class="meta-pill verified">✓ Verified ' + escapeHtml(c.verified || '') + '</span>' +
        '</div>' +
        (noCode
          ? ''
          : '<div class="code-row">' +
              '<div class="code-text">' + escapeHtml(c.code) + '</div>' +
              '<button class="copy-btn" data-code="' + escapeHtml(c.code) + '" data-idx="' + idx + '">Copy Code</button>' +
            '</div>' +
            '<div class="copied-msg" id="copied-msg-' + idx + '">Code copied!</div>'
        ) +
        '<a class="visit-btn" href="' + escapeHtml(c.link || '#') + '" target="_blank" rel="noopener">Visit Store →</a>';

      grid.appendChild(card);
    });

    // wire up copy buttons
    document.querySelectorAll('.copy-btn').forEach(function(btn){
      btn.addEventListener('click', function(){
        const code = btn.getAttribute('data-code');
        const idx = btn.getAttribute('data-idx');
        const msg = document.getElementById('copied-msg-' + idx);

        function showCopied(){
          if(msg){
            msg.style.display = 'block';
            setTimeout(function(){ msg.style.display = 'none'; }, 1800);
          }
        }

        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(code).then(showCopied).catch(function(){
            fallbackCopy(code);
            showCopied();
          });
        } else {
          fallbackCopy(code);
          showCopied();
        }
      });
    });
  }

  function fallbackCopy(text){
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch(e) {}
    document.body.removeChild(ta);
  }

  renderCoupons();

  /* =====================================================================
     ===== WHATSAPP NUMBER (EDIT THIS PART ONLY) =====
     Replace the digits below with your WhatsApp number in international
     format WITHOUT a + sign and WITHOUT spaces.
     Example: for +91 98765 43210 write  919876543210
     ===================================================================== */
  const whatsappNumber = "919999999999"; // <-- CHANGE THIS to your real number
  const whatsappMessage = "Hi, I have a query about a CouponWorld Noida coupon.";
  document.getElementById('wa-float-btn').href =
    "https://wa.me/" + whatsappNumber + "?text=" + encodeURIComponent(whatsappMessage);
</script>

</body>
</html>
