"""
面包多模板测试
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from templates import ALL_TEMPLATES, get_template, list_templates, template_article, template_bundle, template_file_product


class TestTemplates:
    def test_article_structure(self):
        assert "name" in template_article
        assert "fields" in template_article
        f = template_article["fields"]
        assert f["producttype"] == 1
        assert "productcontent" in f
        assert isinstance(f["productprice"], (int, float))

    def test_file_product_structure(self):
        f = template_file_product["fields"]
        assert f["producttype"] == 1
        assert f["buyer_comment"] == 1

    def test_bundle_structure(self):
        f = template_bundle["fields"]
        assert f["producttype"] == 3
        assert f["opendata"] == 1

    def test_get_template_article(self):
        t = get_template("article")
        assert t is not None
        assert "\u56fe\u6587" in t["name"]

    def test_get_template_file(self):
        t = get_template("file")
        assert t is not None

    def test_get_template_bundle(self):
        t = get_template("bundle")
        assert t is not None

    def test_get_template_nonexistent(self):
        assert get_template("nonexistent") is None

    def test_list_templates(self):
        tpl = list_templates()
        assert len(tpl) == 3
        keys = [t["key"] for t in tpl]
        assert "article" in keys
        assert "file" in keys
        assert "bundle" in keys

    def test_all_templates_count(self):
        assert len(ALL_TEMPLATES) == 3

    def test_all_templates_required_fields(self):
        required = ["productname", "producttype", "productdetail", "productimage", "productprice", "category"]
        for name, tpl in ALL_TEMPLATES.items():
            assert "name" in tpl
            assert "description" in tpl
            assert "fields" in tpl
            for f in required:
                assert f in tpl["fields"], f"Template {name} missing {f}"

    def test_valid_categories(self):
        for name, tpl in ALL_TEMPLATES.items():
            assert tpl["fields"]["category"] in range(15)

    def test_valid_product_types(self):
        for name, tpl in ALL_TEMPLATES.items():
            assert tpl["fields"]["producttype"] in {1, 3}
