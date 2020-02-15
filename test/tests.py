import add_parent_to_path
import unittest
from ddt import ddt, data, unpack

from finder import get_posting_links


@ddt
class TestWrangleFuncs(unittest.TestCase):
    @data(
        ("https://www.klipfolio.com/careers", "Marketing", "https://www.klipfolio.com/careers/director-digital-marketing", 1),
        ("https://www.shopify.ca/careers/search?specialties%5B%5D=4&specialties%5B%5D=8&specialties%5B%5D=10&locations%5B%5D=1&keywords=&sort=specialty_asc", "Manager", "https://www.shopify.ca/careers/senior-project-manager-trust-assurance-team-688745", 2),
        ("https://www.shopify.ca/careers/search?keywords=&sort=specialty_asc", "Scientist", "https://www.shopify.ca/careers/senior-data-scientist-multiple-roles-e6a7b8", 4),
        ("https://lixar.com/careers/", "Back-end", "https://lixar.com/lixar-blog/career/back-end-developer/", 1),
    )
    @unpack
    def test_get_posting_links(self, entry, keyword, desired_link, desired_links_count):
        found_links = get_posting_links(entry, keyword)
        self.assertTrue(desired_link in found_links)
        self.assertEqual(desired_links_count, len(found_links))

if __name__ == "__main__":
    unittest.main(verbosity=2)
