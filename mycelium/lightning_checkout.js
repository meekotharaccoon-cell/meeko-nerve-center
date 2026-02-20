/**
 * MEEKO MYCELIUM — LIGHTNING CHECKOUT
 * Cloudflare Worker that creates Strike Lightning invoices.
 * Deploy this to Cloudflare Workers (free tier, 100k req/day).
 * 
 * HOW IT WORKS:
 * 1. Gallery JS calls this worker: POST /invoice {artName, artFile}
 * 2. Worker creates Strike invoice for $1
 * 3. Returns Lightning payment request string
 * 4. Gallery shows QR code + copy button
 * 5. Buyer pays
 * 6. Strike webhook calls /webhook on this worker
 * 7. Worker sends download email to buyer
 * 
 * DEPLOY:
 * 1. Go to workers.cloudflare.com (free account)
 * 2. Create new Worker
 * 3. Paste this code
 * 4. Add env vars: STRIKE_API_KEY, FROM_EMAIL, GMAIL_APP_PASSWORD
 */

const STRIKE_API = 'https://api.strike.me/v1';
const GALLERY_RAW = 'https://raw.githubusercontent.com/meekotharaccoon-cell/gaza-rose-gallery/main/art/';
const GALLERY_URL = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Content-Type': 'application/json'
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, {status: 204, headers});
    }

    // POST /invoice — create Lightning invoice
    if (url.pathname === '/invoice' && request.method === 'POST') {
      const {artName, artFile} = await request.json();
      
      try {
        // Create invoice via Strike API
        const invoiceRes = await fetch(`${STRIKE_API}/invoices`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${env.STRIKE_API_KEY}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            correlationId: `gaza-rose-${Date.now()}`,
            description: `Gaza Rose — ${artName} (300 DPI) — 70% to PCRF`,
            amount: {amount: '1.00', currency: 'USD'}
          })
        });
        
        const invoice = await invoiceRes.json();
        const invoiceId = invoice.invoiceId;
        
        // Get Lightning payment request
        const quoteRes = await fetch(`${STRIKE_API}/invoices/${invoiceId}/quote`, {
          method: 'POST',
          headers: {Authorization: `Bearer ${env.STRIKE_API_KEY}`}
        });
        const quote = await quoteRes.json();
        
        // Store art info for webhook delivery
        await env.PENDING.put(invoiceId, JSON.stringify({artName, artFile}), {expirationTtl: 3600});
        
        return new Response(JSON.stringify({
          invoiceId,
          lnInvoice: quote.lnInvoice,
          expirationInSec: quote.expirationInSec
        }), {headers});
        
      } catch(e) {
        return new Response(JSON.stringify({error: e.message}), {status: 500, headers});
      }
    }

    // POST /webhook — Strike payment notification
    if (url.pathname === '/webhook' && request.method === 'POST') {
      const event = await request.json();
      
      if (event.eventType === 'invoice.updated' && event.data?.state === 'PAID') {
        const invoiceId = event.data.invoiceId;
        const artData = await env.PENDING.get(invoiceId);
        
        if (artData) {
          const {artName, artFile} = JSON.parse(artData);
          const downloadUrl = GALLERY_RAW + encodeURIComponent(artFile);
          
          // Send download email (using simple SMTP via fetch to a mail service)
          // For now, log it — full email sending needs SendGrid or similar
          console.log(`PAID: ${artName} — download: ${downloadUrl}`);
          
          // TODO: Send email to buyer with download link
          // buyer email not available from Lightning — show download link in gallery instead
          
          await env.PENDING.delete(invoiceId);
        }
      }
      
      return new Response('OK', {status: 200});
    }

    // GET /status/:invoiceId — check payment status
    if (url.pathname.startsWith('/status/') && request.method === 'GET') {
      const invoiceId = url.pathname.split('/status/')[1];
      try {
        const res = await fetch(`${STRIKE_API}/invoices/${invoiceId}`, {
          headers: {Authorization: `Bearer ${env.STRIKE_API_KEY}`}
        });
        const data = await res.json();
        return new Response(JSON.stringify({state: data.state}), {headers});
      } catch(e) {
        return new Response(JSON.stringify({error: e.message}), {status: 500, headers});
      }
    }

    return new Response('Gaza Rose Mycelium Worker', {status: 200});
  }
};
