import fs from 'node:fs/promises';
import { SpreadsheetFile, Workbook } from '@oai/artifact-tool';

const repo = 'C:/Users/HP/Documents/Codex/2026-11-26/aa/work/couponword-latest-2';
const outDir = 'C:/Users/HP/Documents/Codex/2026-11-26/aa/outputs/tv-catalogue-20261128';
const asOf = '2026-11-28';
const cat = JSON.parse(await fs.readFile(`${repo}/data/india_tv_earbuds_40_catalogue.json`, 'utf8'));
const pop = JSON.parse(await fs.readFile(`${repo}/data/india_tv_popularity_candidates_2026-11-09.json`, 'utf8'));

const extras = [
  ['Xiaomi','Smart 4K TV F 43 2025','43','https://store.mi.com/in/products/453-0-0-1',26999],
  ['Xiaomi','Smart TV X Series 50 2025','50','https://store.mi.com/in/products/453-0-0-1',29999],
  ['Xiaomi','Smart TV A Series 43 2025','43','https://www.mi.com/in/tv-smart-home/',21999],
  ['Xiaomi','Smart TV X Series 55 2025','55','https://www.mi.com/in/tv-smart-home/',37999],
  ['Xiaomi','Smart TV 32 A GTV','32','https://store.mi.com/in/products/453-0-0-1',14499],
  ['Xiaomi','Smart TV F 32','32','https://store.mi.com/in/products/453-0-0-1',14499],
  ['Xiaomi','TV FX Mini LED 43','43','https://www.mi.com/in/tv-smart-home/',27999],
  ['Xiaomi','Smart TV FX Pro QLED 43','43','https://www.mi.com/in/tv-smart-home/',27499],
  ['Samsung','U8400F Crystal 4K UHD Smart TV 55','55','https://www.samsung.com/in/tvs/help-me-choose/',50990],
  ['Samsung','U8100F Crystal 4K UHD Smart TV 55','55','https://www.samsung.com/in/tvs/help-me-choose/',48990],
  ['Samsung','Q8F QLED 4K Vision AI Smart TV 55','55','https://www.samsung.com/in/tvs/qled-tv/q8f-55-inch-qled-4k-smart-tv-qa55q8faaulxl/',75950],
  ['Samsung','R85H Micro RGB 4K Smart TV 55','55','https://www.samsung.com/in/tvs/micro-rgb/r85h-55-inch-4k-smart-tv-mra55r85haulxl/',130990],
].map(([brand, model, size, url, price]) => ({
  id: `EXTRA_${brand}_${size}_${model.replace(/[^A-Z0-9]+/gi,'_')}`,
  brand, model, model_code:'Not stated', source_url:url, manufacturer_source_url:url,
  indicative_price_inr:price, observed_at:asOf, signal:'OFFICIAL INDIA STOREFRONT / PRODUCT SELECTOR',
  evidence_caveat:'Official India page/selector observed on 2026-11-28; field-level specifications not independently transcribed in this workbook row.',
  specifications:[
    {label:'Size (in)', value:size, source_url:url, evidence:'OFFICIAL_INDIA_PAGE'},
    {label:'Resolution', value:'4K UHD / page not fully field-transcribed', source_url:url, evidence:'OFFICIAL_INDIA_PAGE'},
    {label:'Panel / backlight', value:'See official source page', source_url:url, evidence:'OFFICIAL_INDIA_PAGE'},
    {label:'Smart OS', value:'See official source page', source_url:url, evidence:'OFFICIAL_INDIA_PAGE'},
    {label:'Native refresh rate', value:'Not stated in captured evidence', source_url:url, evidence:'NOT_CAPTURED'},
    {label:'HDR formats', value:'Not stated in captured evidence', source_url:url, evidence:'NOT_CAPTURED'},
    {label:'HDMI / USB', value:'Not stated in captured evidence', source_url:url, evidence:'NOT_CAPTURED'},
    {label:'Audio output', value:'Not stated in captured evidence', source_url:url, evidence:'NOT_CAPTURED'},
  ],
  retailers:{}, product_status:'RESEARCH_ONLY', purchase_cta_eligible:false, performance_ranking_eligible:false, price_ranking_weight:0,
}));

const tv20 = cat.records.filter(x => x.category === 'tvs');
const byKey = new Map();
for (const x of [...tv20, ...pop.records, ...extras]) {
  const key = `${x.brand}|${x.model_code && x.model_code !== 'Not stated' ? x.model_code : x.model}`.toLowerCase();
  if (!byKey.has(key)) byKey.set(key, x);
}
const items = [...byKey.values()].slice(0,50);
if (items.length !== 50) throw new Error(`Expected 50, got ${items.length}`);

const getSpec = (x, labels) => {
  const s = (x.specifications || []).find(v => labels.some(label => String(v.label).toLowerCase().includes(label)));
  return s?.value ?? 'Not stated in source';
};
const url = x => x.manufacturer_source_url || x.source_url || x.technical_source_url || '';
const retailerUrl = (x, store) => x.retailers?.[store]?.retailer_research_url || x.retailers?.[store]?.url || '';
const rows = items.map((x, i) => [i+1, x.brand || '', x.model || '', x.model_code || 'Not stated', getSpec(x,['size']), getSpec(x,['panel','backlight']), getSpec(x,['resolution']), getSpec(x,['native hz','refresh']), getSpec(x,['hdr']), getSpec(x,['smart os','os']), getSpec(x,['hdmi']), getSpec(x,['usb']), getSpec(x,['speaker','audio']), getSpec(x,['ram']), getSpec(x,['storage']), x.indicative_price_inr ?? x.manufacturer_display_price_inr ?? 'Not verified', x.observed_at || x.reviewed_at || asOf, url(x), retailerUrl(x,'amazon'), retailerUrl(x,'flipkart'), retailerUrl(x,'croma'), x.signal || x.source_grade || 'Research catalogue', x.evidence_caveat || 'Only source-supported fields admitted']);

const headers = ['Rank / order','Brand','Model','Model code','Size (in)','Panel / backlight','Resolution','Native refresh','HDR formats','Smart OS','HDMI','USB','Audio output','RAM','Storage','Indicative price (INR)','Observed / checked','Manufacturer or technical source','Amazon research link','Flipkart research link','Croma research link','Selection signal','Evidence / limitations'];
const wb = Workbook.create();
const overview = wb.worksheets.add('Overview');
const sheet = wb.worksheets.add('Top 50 TVs');
const sources = wb.worksheets.add('Sources');
const method = wb.worksheets.add('Method');
for (const s of [overview,sheet,sources,method]) { s.showGridLines = false; }
overview.getRange('A1:F12').values = [
 ['Top 50 India-market TVs — source-linked research workbook','','','','',''],
 ['As of',asOf,'Records',50,'Exact unit-sales ranking verified?',false],
 ['Scope','Current India-market / popularity candidates; not a verified sales leaderboard.','','','',''],
 ['How to use','Use Top 50 TVs for comparison; open source links before publishing price/spec claims.','','','',''],
 ['Price note','Prices are indicative or official storefront observations and can change by pincode, stock and offer.','','','',''],
 ['Quality gate','“Not stated in source” means the field was not captured; it is not a guessed value.','','','',''],
 ['Calculator page','https://coupon-world.in/tvs/tv-size-calculator/','','','',''],
 ['Summary formula','This workbook is traceable to the Top 50 TVs rows and Sources sheet.','','','',''],
 ['','','','','',''],
 ['Model count','=COUNTA(\'Top 50 TVs\'!C2:C51)','','','',''],
 ['Rows with official source','=COUNTIF(\'Top 50 TVs\'!R2:R51,"<>")','','','',''],
 ['Rows with live price verification','0','','','',''],
 ];
sheet.getRange('A1:W51').values = [headers, ...rows];
sheet.freezePanes.freezeRows(1); sheet.freezePanes.freezeColumns(4);
sources.getRange('A1:E1').values = [['Record','Model','Source type','URL','What it supports']];
const sourceRows=[]; items.forEach((x,i)=>{ const all=[['Manufacturer / technical',url(x),'identity and captured technical fields'],['Amazon research',retailerUrl(x,'amazon'),'research link only; not live offer'],['Flipkart research',retailerUrl(x,'flipkart'),'research link only; not live offer'],['Croma research',retailerUrl(x,'croma'),'research link only; not live offer']]; all.filter(v=>v[1]).forEach(v=>sourceRows.push([i+1,x.model,v[0],v[1],v[2]])); });
sources.getRange(`A2:E${sourceRows.length+1}`).values = sourceRows;
method.getRange('A1:B16').values = [
 ['Method and quality notes',''],
 ['Selection basis','20 existing catalogue records + 20 popularity candidates + 12 additional official India storefront/product-selector records, deduplicated to 50.'],
 ['Sales-rank warning','No public source in the research set verifies unit sales for every model; do not call this “India best-selling top 50”.'],
 ['Specs policy','Only captured source fields are imported. Missing fields remain “Not stated in source”; no values are inferred.'],
 ['Price policy','Indicative/storefront price only. Verify live payable price, pincode, stock and warranty before publishing.'],
 ['Retailer links','Amazon/Flipkart/Croma links are research links unless the record explicitly says exact model link verified.'],
 ['TV-size model','Target diagonal ≈ 0.62 × viewing distance in inches for mixed use; capped by wall clearance and snapped down to 32/43/50/55/65/75/85/98.'],
 ['Wall clearance','Preview assumes 6 inches side and 8 inches top clearance; exact installation requires model dimensions and mount checks.'],
 ['Aspect ratio','Width ≈ diagonal × 0.8716 and height ≈ diagonal × 0.4903 for a 16:9 screen, before bezel/stand.'],
 ['Site route','https://coupon-world.in/tvs/tv-size-calculator/'],
 ['Checked date',asOf],
 ['Next refresh','Recheck prices, stock and source pages before each editorial update.'],
 ['Publication status','Research workbook; not a purchase feed or automated price guarantee.'],
 ['Source priority','Manufacturer India pages > exact retailer detail pages > retailer/search/category references.'],
 ['Workbook owner','Coupon World editorial / SEO research'],
 ['End of notes',''],
 ];

const titleFmt = {font:{name:'Arial',size:14,bold:true,color:'#0F172A'}};
overview.getRange('A1:F1').format = {font:{name:'Arial',size:14,bold:true,color:'#0F172A'}};
for (const s of [sheet,sources,method]) s.getRange('A1:Z1').format = {fill:'#123B5D',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,verticalAlignment:'center'};
overview.getRange('A1:F12').format.font = {name:'Arial',size:10,color:'#1F2937'};
overview.getRange('A1:F1').format.font = titleFmt.font;
sheet.getRange('A2:W51').format = {font:{name:'Arial',size:9,color:'#1F2937'},wrapText:true,verticalAlignment:'center'};
sources.getRange(`A2:E${sourceRows.length+1}`).format = {font:{name:'Arial',size:9,color:'#1F2937'},wrapText:true,verticalAlignment:'center'};
method.getRange('A2:B16').format = {font:{name:'Arial',size:10,color:'#1F2937'},wrapText:true,verticalAlignment:'top'};
sheet.getRange('P2:P51').format.numberFormat = '#,##0';
sheet.getRange('A1:W51').format.borders = {preset:'inside',style:'thin',color:'#E2E8F0'};
sheet.getRange('A1:W51').format.autofitColumns();
sources.getRange('A1:E100').format.autofitColumns();
method.getRange('A1:B16').format.autofitColumns();
sheet.getRange('A1:W1').format.rowHeight = 34;
sheet.getRange('A1:W51').format.rowHeight = 36;
sheet.getRange('A1:W51').format.columnWidth = 16;
sheet.getRange('C1:C51').format.columnWidth = 28; sheet.getRange('R1:U51').format.columnWidth = 32; sheet.getRange('W1:W51').format.columnWidth = 34;
sources.getRange(`D1:D${sourceRows.length+1}`).format.columnWidth = 48; sources.getRange(`E1:E${sourceRows.length+1}`).format.columnWidth = 28;
method.getRange('A1:A16').format.columnWidth = 24; method.getRange('B1:B16').format.columnWidth = 95;
wb.recalculate();
await fs.mkdir(outDir,{recursive:true});
for (const [name, sheetName] of [['overview','Overview'],['top50','Top 50 TVs'],['method','Method']]) {
  const preview = await wb.render({sheetName, autoCrop:'all', scale:1, format:'png'});
  await fs.writeFile(`${outDir}/${name}.png`, new Uint8Array(await preview.arrayBuffer()));
}
const xlsx = await SpreadsheetFile.exportXlsx(wb); await xlsx.save(`${outDir}/top-50-india-tvs.xlsx`);
console.log(JSON.stringify({out:`${outDir}/top-50-india-tvs.xlsx`,count:items.length,sources:sourceRows.length}));
