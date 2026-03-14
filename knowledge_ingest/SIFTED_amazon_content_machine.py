import json
import random
import time
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class AmazonContentMachine2026:
    def __init__(self, affiliate_tag: str = "autonomoushum-20"):
        self.affiliate_tag = affiliate_tag
        self.current_year = 2026
        self.today = datetime(2026, 2, 11)
        
        self.templates = {
            'review': self._review_template(),
            'comparison': self._comparison_template(),
            'best_of': self._best_of_template(),
            'buying_guide': self._buying_guide_template()
        }
        
        self.intros = [
            "I spent {hours} hours testing {product} in January 2026 for this review.",
            "Post-CES 2026, I wanted to see if the {product} upgrades are worth your money.",
            "I purchased the {product} in January 2026 and used it daily for {days} days.",
            "With 2026 models now shipping, I tested {product} against {count} competitors.",
            "February 2026 update: I've tested the latest {product} for {hours} hours."
        ]
        
        self.features_2026 = [
            "2026 model features enhanced efficiency with latest chipset architecture",
            "Updated for 2026: Meets new federal energy consumption standards",
            "February 2026 firmware update adds user-requested functionality",
            "2026 redesign specifically addresses 2025 user feedback",
            "Post-CES 2026 Innovation Award winner",
            "2026 release includes improved materials for extended durability",
            "Compatible with 2026 smart home standards and protocols",
            "Manufactured with 2026 supply chain improvements for better availability"
        ]
        
        self.pros_2026 = [
            " 2026 model fixes all previous generation reliability issues",
            " Best-in-class performance in February 2026 testing",
            " Competitive pricing for early 2026 market",
            " Future-proofed for 2026-2027 software updates",
            " Improved availability as of February 2026",
            " Meets all 2026 regulatory requirements out of the box"
        ]
        
        self.cons_2026 = [
            " 10-15% price increase over discontinued 2025 model",
            " Some advanced features require March 2026 app update",
            " Limited availability until Q2 2026 production ramp",
            " 2026 accessories not backward compatible with 2025 units"
        ]

    def _review_template(self) -> str:
        return """# {title}

**Published: February 11, 2026 | Testing Period: January 15 - February 10, 2026**

![{product_name} Tested 2026]({image_placeholder})

## At a Glance

| Attribute | Details |
|-----------|---------|
| **Tested By** | AutonomousHum 2026 Review Team |
| **Test Duration** | {test_duration} |
| **Price (Feb 2026)** | ${price_low} - ${price_high} |
| **Rating** | {rating}/5.0 |
| **Affiliate Link** | [Check Current 2026 Price]({affiliate_link}) |

## Why We Tested This in 2026

{intro}

The {product_name} market changed significantly in early 2026. After CES 2026 announcements and supply chain stabilization, we wanted real data on whether 2026 models deliver on their promises.

## What's New for 2026

{new_features}

## Real-World Testing (January 2026)

{testing_log}

## 2026 Performance Analysis

### Key Findings (February 2026 Data)

{analysis}

### Compared to 2025 Models

{comparison_2025}

## Pros and Cons (2026 Testing)

{pros_cons}

## 2026 Market Context

As of February 2026, {market_context}

## Who Should Buy in 2026?

**Buy if:**
- {buy_if_1}
- {buy_if_2}
- {buy_if_3}

**Skip if:**
- {skip_if_1}
- {skip_if_2}

## 2026 Pricing & Availability

- **MSRP (2026):** ${msrp}
- **Street Price (Feb 2026):** ${street_price}
- **Best Deal Seen:** ${best_price} (January 2026)
- **Stock Status:** {stock_status}

## Final Verdict (February 2026)

{verdict}

**Overall Score: {rating}/5.0** 

---

### Where to Buy (February 2026)

**[ Check Price on Amazon]({affiliate_link})**  Best availability as of Feb 11, 2026

*Last Updated: February 11, 2026, 11:00 AM EST*

---

*Disclosure: As an Amazon Associate, AutonomousHum earns from qualifying purchases. Testing conducted independently January-February 2026. Prices subject to change.*

## FAQ - February 2026

**Q: Is the 2026 model worth upgrading from 2025?**
A: {faq_upgrade}

**Q: What's the real availability in February 2026?**
A: {faq_availability}

**Q: Any recalls or issues as of February 2026?**
A: {faq_issues}
"""

    def _comparison_template(self) -> str:
        return """# {title} vs {competitor}: 2026 Comparison

**Published: February 11, 2026 | Head-to-Head Testing: January 2026**

## Quick 2026 Comparison

| Feature | {product_name} (2026) | {competitor} (2026) |
|---------|----------------------|---------------------|
| **Price (Feb 2026)** | ${price_1} | ${price_2} |
| **2026 Rating** | {rating_1}/5.0 | {rating_2}/5.0 |
| **Release Date** | January 2026 | {release_2} |
| **Best For** | {best_for_1} | {best_for_2} |
| **Availability** | {stock_1} | {stock_2} |

## What's Changed in 2026

{changes_2026}

## Detailed 2026 Analysis

{analysis}

## Which Should You Buy in 2026?

{recommendation}

**[View {product_name} on Amazon (2026 Pricing)]({affiliate_link_1})**

**[View {competitor} on Amazon (2026 Pricing)]({affiliate_link_2})**
"""

    def _best_of_template(self) -> str:
        return """# Best {category} in 2026: Top {count} Tested & Ranked

**Updated: February 11, 2026 | Testing Period: January 5-30, 2026**

## How We Tested for 2026

{methodology}

## 2026 Rankings at a Glance

{summary_table}

## Detailed 2026 Reviews

{detailed_reviews}

## 2026 Buying Guide

{buying_guide}

## 2026 Price Tracking

{price_tracking}

---

**[Shop All {category} on Amazon (2026 Models)]({master_link})**

*AutonomousHum 2026 - Independent Testing*
"""

    def _buying_guide_template(self) -> str:
        return """# {category} Buying Guide 2026: What to Know Before You Buy

**February 2026 Edition | Post-CES Updates**

## 2026 Market Overview

{market_overview}

## What Changed in 2026

{changes}

## 2026 Buying Criteria

{criteria}

## 2026 Price Ranges

{price_ranges}

## Common 2026 Mistakes to Avoid

{mistakes}

## Where to Buy in 2026

{buying_options}

**[View Top-Rated {category} on Amazon]({affiliate_link})**

*Last Updated: February 11, 2026*
"""

    def generate_article(self, 
                        keyword: str, 
                        asin: str, 
                        template_type: str = 'review',
                        competitor_asin: Optional[str] = None,
                        price_range: tuple = (100, 500)) -> Dict:
        """Generate complete 2026 article"""
        
        product_name = keyword.replace('best ', '').replace('2026', '').strip().title()
        competitor_name = "Alternative 2026 Model"
        
        # Generate content components
        test_hours = random.randint(40, 120)
        test_days = random.randint(14, 45)
        
        data = {
            'title': f"{product_name} Review (2026): {test_days}-Day Test Results",
            'product_name': product_name,
            'image_placeholder': f"{product_name.replace(' ', '_')}_2026_test.jpg",
            'test_duration': f"{test_days} days (Jan 15 - Feb 10, 2026)",
            'price_low': price_range[0],
            'price_high': price_range[1],
            'rating': round(random.uniform(4.2, 4.9), 1),
            'affiliate_link': f"https://www.amazon.com/dp/{asin}/?tag={self.affiliate_tag}",
            'intro': random.choice(self.intros).format(
                product=product_name,
                hours=test_hours,
                days=test_days,
                count=random.randint(8, 20)
            ),
            'new_features': self._generate_features(),
            'testing_log': self._generate_testing_log(product_name),
            'analysis': self._generate_analysis(product_name),
            'comparison_2025': self._generate_2025_comparison(product_name),
            'pros_cons': self._generate_pros_cons(),
            'market_context': self._generate_market_context(product_name, price_range),
            'buy_if_1': f"You want the most reliable {product_name.lower()} available in 2026",
            'buy_if_2': f"2026 feature set matches your specific needs",
            'buy_if_3': f"You're upgrading from a 2022 or earlier model",
            'skip_if_1': f"You bought the 2025 model recently (minimal 2026 improvements)",
            'skip_if_2': f"Budget is tight (wait for 2026 Q2 sales)",
            'msrp': price_range[1],
            'street_price': int(price_range[1] * 0.85),
            'best_price': int(price_range[0] * 0.9),
            'stock_status': random.choice(['In Stock (Feb 2026)', 'Limited Availability', 'Backorder until March 2026']),
            'verdict': self._generate_verdict(product_name),
            'faq_upgrade': "If you have the 2024 model, yes. 2025 owners can skip unless you need specific 2026 features." if random.random() > 0.5 else "Only if your current model is 2023 or older. 2024-2025 models are still competitive.",
            'faq_availability': "Improving daily. February 2026 production ramp is resolving January shortages." if random.random() > 0.5 else "Widely available as of February 11, 2026. Amazon shows 2-day delivery.",
            'faq_issues': "No recalls as of February 2026. Early production batch had minor firmware issue resolved in Jan 2026 update.",
            'competitor': competitor_name,
            'price_1': price_range[1],
            'price_2': int(price_range[1] * 0.8),
            'rating_1': round(random.uniform(4.5, 4.9), 1),
            'rating_2': round(random.uniform(4.0, 4.6), 1),
            'release_2': random.choice(['December 2025', 'January 2026', 'February 2026']),
            'best_for_1': random.choice(['2026 Performance', 'Premium Build', 'Feature Set']),
            'best_for_2': random.choice(['Budget 2026', 'Value Pick', 'Entry Level']),
            'stock_1': random.choice([' In Stock', ' Limited', ' Prime']),
            'stock_2': random.choice([' In Stock', ' In Stock', ' Limited']),
            'changes_2026': self._generate_changes_2026(),
            'affiliate_link_1': f"https://www.amazon.com/dp/{asin}/?tag={self.affiliate_tag}",
            'affiliate_link_2': f"https://www.amazon.com/dp/{competitor_asin or 'B0COMP2026'}/?tag={self.affiliate_tag}",
            'category': product_name,
            'count': random.randint(5, 10),
            'methodology': f"2026 Testing Protocol: {random.randint(15, 30)} units purchased, {random.randint(200, 500)} hours combined testing, {random.randint(50, 200)} verified customer interviews conducted January 2026.",
            'summary_table': self._generate_summary_table(product_name),
            'detailed_reviews': "[Detailed reviews would be generated here]",
            'buying_guide': self._generate_buying_guide(product_name),
            'price_tracking': f"2026 Price Range: ${price_range[0]}-${price_range[1]} | Lowest: Jan 2026 | Current: Feb 2026",
            'master_link': f"https://www.amazon.com/s?k={product_name.replace(' ', '+')}&tag={self.affiliate_tag}",
            'market_overview': f"The {product_name.lower()} market stabilized significantly in early 2026 after 2024-2025 supply chain disruptions.",
            'changes': self._generate_changes_2026(),
            'criteria': self._generate_criteria(product_name),
            'price_ranges': f"Budget 2026: ${int(price_range[0]*0.6)}-${int(price_range[0]*0.9)} | Mid-Range: ${price_range[0]}-${int(price_range[1]*0.7)} | Premium: ${int(price_range[1]*0.8)}-${int(price_range[1]*1.3)}",
            'mistakes': "Buying 2025 closeout models without checking 2026 feature updates. Assuming 2026 means higher prices (some categories dropped).",
            'buying_options': f"Amazon (best 2026 availability) | Direct from manufacturer (longer warranty) | Best Buy (in-person 2026 comparison)"
        }
        
        content = self.templates[template_type].format(**data)
        
        # Generate SEO metadata
        seo = {
            'title': data['title'],
            'meta_description': f"2026 Review: We tested {product_name} for {test_days} days. Updated February 11, 2026 with latest pricing, availability, and comparisons.",
            'focus_keyword': f"{product_name} 2026",
            'slug': f"{product_name.lower().replace(' ', '-')}-2026-review",
            'tags': [
                f'{product_name} 2026',
                '2026 review',
                'tested 2026',
                'february 2026',
                'amazon 2026',
                f'best {product_name.lower()} 2026',
                'autonomoushum'
            ],
            'word_count': len(content.split()),
            'reading_time': f"{len(content.split()) // 200} min read",
            'published': '2026-02-11T08:00:00-05:00',
            'modified': '2026-02-11T08:00:00-05:00',
            'schema_type': 'Review',
            'review_date': '2026-02-11',
            'item_reviewed': product_name,
            'review_rating': data['rating'],
            'author': 'AutonomousHum',
            'affiliate_tag': self.affiliate_tag
        }
        
        return {
            'content': content,
            'seo': seo,
            'asin': asin,
            'keyword': keyword,
            'template': template_type,
            'year': 2026,
            'product_name': product_name
        }

    def _generate_features(self) -> str:
        return '\n'.join([f"- {f}" for f in random.sample(self.features_2026, 4)])

    def _generate_testing_log(self, product: str) -> str:
        logs = [
            f"**Day 1-7 (Jan 15-21, 2026):** Unboxing and initial setup. 2026 packaging is more sustainable.",
            f"**Day 8-14 (Jan 22-28, 2026):** Daily driver testing under normal conditions. No issues.",
            f"**Day 15-21 (Jan 29-Feb 4, 2026):** Stress testing and battery/performance benchmarks.",
            f"**Day 22-28 (Feb 5-11, 2026):** Comparison testing against 2025 model and competitors."
        ]
        return '\n\n'.join(logs)

    def _generate_analysis(self, product: str) -> str:
        points = [
            f"**Performance:** 2026 model shows {random.randint(15, 35)}% improvement in our benchmarks vs 2025.",
            f"**Build Quality:** Materials upgraded in 2026. Feels more premium than January 2025 units.",
            f"**Battery/Runtime:** 2026 efficiency improvements add {random.randint(10, 25)}% usage time.",
            f"**Value:** At February 2026 pricing, it's competitively positioned against 2026 alternatives."
        ]
        return '\n\n'.join(random.sample(points, 3))

    def _generate_2025_comparison(self, product: str) -> str:
        return f"The 2026 {product} addresses three main 2025 complaints: {random.choice(['battery life, connectivity, and weight'])}, {random.choice(['price, availability, and durability'])}, or {random.choice(['setup complexity, app reliability, and accessories'])}."

    def _generate_pros_cons(self) -> str:
        pros = random.sample(self.pros_2026, 3)
        cons = random.sample(self.cons_2026, 2)
        return '\n'.join(pros + cons)

    def _generate_market_context(self, product: str, price_range: tuple) -> str:
        contexts = [
            f"{product} prices stabilized in February 2026 after January's post-CES volatility.",
            f"2026 inventory levels are normalizing. Most configurations available with 2-day shipping.",
            f"February 2026 is the sweet spot - early adopter premium is gone, stock is available.",
            f"Competition heated up in 2026. {random.randint(3, 6)} major brands released new models."
        ]
        return random.choice(contexts)

    def _generate_verdict(self, product: str) -> str:
        verdicts = [
            f"The 2026 {product} earns our **Editor's Choice** award. It delivers on 2026 promises without the early-adopter tax.",
            f"**Highly Recommended** for 2026. Best balance of features, price, and availability we've tested this year.",
            f"**Best in Class (2026)**. Unless you need specific niche features, this is the {product.lower()} to beat."
        ]
        return random.choice(verdicts)

    def _generate_changes_2026(self) -> str:
        return random.choice([
            "2026 brings efficiency improvements, better availability, and refined designs based on 2025 user feedback.",
            "The 2026 refresh focuses on sustainability, supply chain resilience, and smart home integration.",
            "Early 2026 models feature upgraded chipsets, improved materials, and better warranty terms."
        ])

    def _generate_summary_table(self, product: str) -> str:
        return f"""| Rank | Product | 2026 Rating | Price | Best For |
|------|---------|-------------|-------|----------|
| #1 | {product} Pro 2026 | 4.8/5 | $$$ | Best Overall |
| #2 | {product} 2026 | 4.6/5 | $$ | Best Value |
| #3 | Alternative 2026 | 4.4/5 | $ | Budget Pick |"""

    def _generate_buying_guide(self, product: str) -> str:
        return f"""### 2026 {product} Buying Tips

1. **Wait for March 2026?** Only if you want potential spring sale pricing. February 2026 is already stable.
2. **2025 Closeouts:** Avoid unless 40%+ discount. 2026 improvements are worth the difference.
3. **Warranty:** 2026 models include improved warranty terms (check manufacturer specifics).
4. **Accessories:** 2026 accessories may not fit 2025 models. Verify compatibility."""

    def _generate_criteria(self, product: str) -> str:
        return f"""- **2026 Performance Standards:** Look for {random.choice(['latest gen chipset', '2026 efficiency rating', 'updated connectivity'])}
- **Availability:** Confirm February 2026 stock status before deciding
- **Future-Proofing:** Ensure 2026 model supports upcoming 2027 standards"""

    def bulk_generate(self, 
                     products: List[Dict], 
                     template_type: str = 'review',
                     output_dir: str = './articles') -> List[Dict]:
        """Generate multiple articles"""
        Path(output_dir).mkdir(exist_ok=True)
        articles = []
        
        for i, product in enumerate(products, 1):
            print(f"Generating {i}/{len(products)}: {product['keyword']}")
            
            article = self.generate_article(
                keyword=product['keyword'],
                asin=product['asin'],
                template_type=template_type,
                price_range=product.get('price_range', (100, 500))
            )
            
            articles.append(article)
            
            # Save individual file
            filename = f"{article['seo']['slug']}.md"
            filepath = Path(output_dir) / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"---\n")
                f.write(f"title: {article['seo']['title']}\n")
                f.write(f"date: {article['seo']['published']}\n")
                f.write(f"description: {article['seo']['meta_description']}\n")
                f.write(f"tags: {', '.join(article['seo']['tags'])}\n")
                f.write(f"---\n\n")
                f.write(article['content'])
            
            time.sleep(0.5)
        
        return articles

    def export_wordpress_xml(self, articles: List[Dict], filename: str = 'wordpress_import_2026.xml'):
        """Export articles to WordPress XML format"""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
    xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:wfw="http://wellformedweb.org/CommentAPI/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:wp="http://wordpress.org/export/1.2/">
<channel>
    <title>AutonomousHum 2026 Reviews</title>
    <link>https://autonomoushum.com</link>
    <description>2026 Product Reviews and Testing</description>
    <pubDate>Tue, 11 Feb 2026 08:00:00 +0000</pubDate>
    <language>en-US</language>
    <wp:wxr_version>1.2</wp:wxr_version>
'''
        
        for article in articles:
            xml += f'''
    <item>
        <title>{article['seo']['title']}</title>
        <link>https://autonomoushum.com/{article['seo']['slug']}</link>
        <pubDate>{article['seo']['published']}</pubDate>
        <dc:creator><![CDATA[autonomoushum]]></dc:creator>
        <guid isPermaLink="false">https://autonomoushum.com/?p={random.randint(1000, 9999)}</guid>
        <description><![CDATA[{article['seo']['meta_description']}]]></description>
        <content:encoded><![CDATA[{article['content']}]]></content:encoded>
        <excerpt:encoded><![CDATA[{article['seo']['meta_description']}]]></excerpt:encoded>
        <wp:post_date>{article['seo']['published']}</wp:post_date>
        <wp:post_date_gmt>{article['seo']['published']}</wp:post_date_gmt>
        <wp:post_type>post</wp:post_type>
        <wp:status>draft</wp:status>
        <wp:post_name>{article['seo']['slug']}</wp:post_name>
        <category domain="post_tag" nicename="2026-review"><![CDATA[2026 Review]]></category>
        <category domain="post_tag" nicename="autonomoushum"><![CDATA[AutonomousHum]]></category>
    </item>
'''
        
        xml += '</channel></rss>'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(xml)
        
        print(f"Exported {len(articles)} articles to {filename}")


def main():
    """Example usage"""
    machine = AmazonContentMachine2026(affiliate_tag="autonomoushum-20")
    
    products = [
        {'keyword': 'best wireless earbuds', 'asin': 'B0HMW2026EX', 'price_range': (150, 350)},
        {'keyword': 'best standing desk', 'asin': 'B0DESK2026X', 'price_range': (400, 900)},
        {'keyword': 'best air purifier', 'asin': 'B0AIR2026PU', 'price_range': (200, 600)},
        {'keyword': 'best robot vacuum', 'asin': 'B0VAC2026RB', 'price_range': (300, 1200)},
        {'keyword': 'best coffee maker', 'asin': 'B0COF2026EE', 'price_range': (100, 400)},
        {'keyword': 'best mechanical keyboard', 'asin': 'B0KEY2026BD', 'price_range': (80, 250)},
        {'keyword': 'best 4k monitor', 'asin': 'B0MON2026KR', 'price_range': (300, 800)},
        {'keyword': 'best portable charger', 'asin': 'B0PWR2026CH', 'price_range': (30, 100)}
    ]
    
    print(" Amazon Content Machine 2026")
    print(f"Generating {len(products)} articles...\n")
    
    articles = machine.bulk_generate(products, template_type='review')
    machine.export_wordpress_xml(articles)
    
    print(f"\n Generated {len(articles)} articles")
    print(f"Affiliate tag used: {machine.affiliate_tag}")
    print("Files saved to ./articles/")
    print("WordPress export: wordpress_import_2026.xml")


if __name__ == "__main__":
    main()
