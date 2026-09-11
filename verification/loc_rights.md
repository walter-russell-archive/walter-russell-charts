# LoC rights & terms — verbatim capture (R7)

Prepared 2026-09-11 (project item R7). This is the verbatim capture of the Library of Congress rights and terms for the 1926 scan, taken from the item record, the collection rights page, and the general legal page. It supports the rights statement on the methods page and the credit line carried with every facsimile. All text below was retrieved 2026-09-11 unless noted.

## 1. Item-level rights statement — `gdc.27004508`

Source: `https://www.loc.gov/item/27004508/?fo=json`, field `item.rights` (retrieved 2026-09-11 via curl; JSON payload, HTML markup preserved as delivered):

```html
<p>The books in this collection are in the public domain and are free to use and reuse.</p>
<p>Credit Line: Library of Congress</p>
<p>More about <a href="/legal/">Copyright and other Restrictions</a>.</p>
<p>For guidance about compiling full citations consult <a href="https://www.loc.gov/teachers/usingprimarysources/citing.html">Citing Primary Sources</a>.</p>
```

## 2. Collection rights-and-access page — Selected Digitized Books

Canonical URL: `https://www.loc.gov/collections/selected-digitized-books/about-this-collection/rights-and-access/`
Direct fetch on 2026-09-11 returned a bot-challenge page ("Just a moment... Enable JavaScript and cookies to continue"); text was captured instead from the Wayback Machine snapshot of 2025-12-23:
`https://web.archive.org/web/20251223073922/https://www.loc.gov/collections/selected-digitized-books/about-this-collection/rights-and-access/` (retrieved 2026-09-11).

Verbatim body under the heading "Rights and Access":

> The books in this collection are in the public domain and are free to use and reuse.
>
> Credit Line: Library of Congress
>
> More about Copyright and other Restrictions.
>
> For guidance about compiling full citations consult Citing Primary Sources.

(The page's own `meta-description` is identical: "The books in this collection are in the public domain and are free to use and reuse.")

This is byte-identical in substance to the item-level statement in §1 — the item statement IS the collection statement.

## 3. LoC general legal page — loc.gov/legal

Source: `https://www.loc.gov/legal/` (retrieved directly 2026-09-11; page dated "December 17, 2020"). Relevant section verbatim:

> ## About Copyright and the Collections
>
> As a publicly supported institution, we generally do not own the rights to materials in our collections. You should determine for yourself whether or not an item is protected by copyright or in the public domain, and then satisfy any copyright or use restrictions when publishing or distributing materials from our collections. Transmission or reproduction of protected items beyond what is allowed by fair use or other exemptions requires written permission from the copyright holder.
>
> If you have more information about material on our websites or are able to provide specific, additional information about the copyright status of a particular item in our collection, please contact us at https://ask.loc.gov/ or at the address listed in the "About this Collection" entry for the item. If you are the copyright holder and believe our websites have not properly attributed your work or have used it without permission, please contact Legal@loc.gov with your contact information and a link to the relevant content.

Also on that page (General Disclaimer, verbatim first sentence): "Materials displayed on our websites are intended for reference use only." — this is a general reference-use framing, not a use restriction on public-domain collection items; the collection-level statement in §2 ("free to use and reuse") is the operative, more specific term for this item.

Rate-limit condition worth honoring during any further tile fetching (loc.gov/legal, "Security" section, verbatim): "Current guidelines recommend that software programs submit a total of no more than 10 requests per minute to our applications, regardless of the number of machines used to submit requests."

## 4. Conditions touching commercial use

- No commercial-use restriction appears anywhere in the item rights statement, the collection rights-and-access page, or loc.gov/legal for public-domain items. The collection statement says "free to use and reuse" without qualification (sources §1–§2, retrieved 2026-09-11).
- LoC's only stated ask is the credit line ("Credit Line: Library of Congress") and self-responsibility for copyright determination (§3).
- [INFERENCE] Since the underlying work is c1926 (copyright page: "Copyright 1926 by Walter Russell", LoC scan image 0008, `https://tile.loc.gov/storage-services/public/gdc/27004508/0008.alto.xml`, retrieved 2026-09-11) and LoC classifies the whole collection as public domain, commercial republication of the 1926 scan is unrestricted on LoC's side. Copyright-renewal status is not analysed here.

## 5. Credit line as it will appear

On each facsimile plate/page (short form):

> Library of Congress

Recommended fuller credit for the edition's front matter (composed from LoC's citation guidance, `cite_this.chicago` field of the item JSON, retrieved 2026-09-11):

> Reproduced from Walter Russell, *The Universal One* (New York: Brieger Press, Inc., c1926), Library of Congress, General Collections, call number Q173 .R85, digitized copy at https://www.loc.gov/item/27004508/. The Library of Congress states that the books in its Selected Digitized Books collection "are in the public domain and are free to use and reuse." Credit Line: Library of Congress.

LoC's own APA-style citation for the item (verbatim from `cite_this.apa`, retrieved 2026-09-11):

> Russell, W., Russell, L., ed. (1926) The universal One; an exact science of the one visible and invisible universe of mind and the registration of all idea of thinking mind in light, which is matter and also energy. [New York, N.Y., Brieger press, inc] [Pdf] Retrieved from the Library of Congress, https://www.loc.gov/item/27004508/.
