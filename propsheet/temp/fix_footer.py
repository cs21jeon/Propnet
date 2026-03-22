#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/landing.html"
with open(path, "r") as f:
    content = f.read()

# Replace footer style
old_footer_style = """        .footer {
            margin-top: 60px;
            font-size: 12px;
            color: #bbb;
        }"""

new_footer_style = """        .footer {
            margin-top: 80px;
            padding-top: 32px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
        }

        .footer-logo {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-bottom: 12px;
        }

        .footer-logo img {
            height: 28px;
        }

        .footer-logo span {
            font-size: 16px;
            font-weight: 600;
            color: #555;
        }

        .footer-info {
            font-size: 12px;
            color: #999;
            line-height: 1.8;
        }

        .footer-info a {
            color: #888;
            text-decoration: none;
        }

        .footer-info a:hover {
            color: #2E86DE;
        }

        .footer-copyright {
            margin-top: 12px;
            font-size: 11px;
            color: #bbb;
        }"""

content = content.replace(old_footer_style, new_footer_style)

# Replace footer HTML
old_footer_html = """        <div class="footer">
            &copy; 2026 Propsheet by GoldenRabbit
        </div>"""

new_footer_html = """        <div class="footer">
            <div class="footer-logo">
                <img src="/propsheet/static/images/propnet-icon.png" alt="Propnet">
                <span>Propnet</span>
            </div>
            <div class="footer-info">
                <a href="mailto:cs21.jeon@gmail.com">cs21.jeon@gmail.com</a><br>
                Propsheet by Propnet
            </div>
            <div class="footer-copyright">
                &copy; 2026 Propnet. All rights reserved.
            </div>
        </div>"""

content = content.replace(old_footer_html, new_footer_html)

with open(path, "w") as f:
    f.write(content)

print("OK - Footer updated with Propnet info")
