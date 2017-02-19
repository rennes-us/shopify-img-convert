#!/usr/bin/env python

"""Some basic tests to run on a development store."""

import unittest
import shopify
import shopify_img_convert
import tempfile
import subprocess
import random
import sys

try:
    from ConfigParser import SafeConfigParser # Python 2
except ImportError:
    from configparser import SafeConfigParser # Python 3

CONFIG = SafeConfigParser()
CONFIG.read('shopify_img_convert.ini')
CONFIG_TEST = dict(CONFIG.items('test'))

shopify_img_convert.auth(**CONFIG_TEST)

def setUpImage(i):
    attrs = {'position': i}
    image_new = shopify.Image(attributes=attrs)
    f = tempfile.NamedTemporaryFile()
    r = tuple([random.randint(0,255) for x in range(3)])
    cmd = ['convert', '-size', '1024x768', 'xc:rgb(%d, %d, %d)' % r, '-gravity', 'center', '-pointsize', '200', '-draw', "text 0,0 '%d'" % i, 'png:%s' % f.name]
    subprocess.check_output(cmd)
    image_new.attach_image(data=f.read(), filename='IMG_%d.png' % i)
    f.close()
    return image_new

def setUpRandomProducts():
    wordfile = '/usr/share/dict/american-english'
    try:
        with open(wordfile) as f:
            words = f.readlines()
    except:
        words = None
    for i in range(2):
        if words:
            title = ' '.join([random.choice(words) for x in range(3)])
        else:
            title = str(i)
        p = randomProduct(title)
        p.save()

def randomProduct(title):
    images = []
    for i in range(random.randint(1,4)):
        images.append(setUpImage(i+1))
    variants = []
    variants.append(shopify.Variant({'price': random.randint(1,100)}))
    attrs = {}
    attrs['title'] = title
    attrs['tags'] = ['bits and bobs, hats']
    attrs['body_html'] = '<p>Hat in Grey. 100% Alpaca.</p>'
    attrs['image'] = images[0]
    attrs['images'] = images
    attrs['variants'] = variants
    product = shopify.Product(attributes=attrs)
    return product

def remove_all_products():
    num_prods = 1
    products = []
    page = 1
    while num_prods:
        prods = shopify.Product.find(page=page, limit=250)
        products.extend(prods)
        num_prods = len(prods)
        page += 1
    for p in products:
        p.destroy()


class TestRandomProducts(unittest.TestCase):

    def tearDown(self):
        remove_all_products()

    def setUp(self):
        setUpRandomProducts()

    def test_is_png(self):
        # all images should be png before and jpg after
        products = shopify_img_convert.get_products()
        for image in products[0].images:
            self.assertTrue(shopify_img_convert.is_png(image.src))
        shopify_img_convert.convert_all_products(quiet=True, path=CONFIG_TEST['store'])
        products = shopify_img_convert.get_products()
        for image in products[0].images:
            self.assertFalse(shopify_img_convert.is_png(image.src))

    def test_convert_all_products(self):
        products = shopify_img_convert.get_products()
        # number of products should not change
        num_prods = len(products)
        shopify_img_convert.convert_all_products(quiet=True, path=CONFIG_TEST['store'])
        products = shopify_img_convert.get_products()
        self.assertEqual(len(products), num_prods)
        # product attributes should not change, except for 'updated_at'
        for i in range(num_prods):
            attrs = {}
            attrs.update(products[i].attributes)
            del attrs['updated_at']
            attrs_new = {}
            attrs_new.update(products[i].attributes)
            del attrs_new['updated_at']
            self.assertEqual(attrs_new, attrs)


class TestEmptySet(unittest.TestCase):

    def tearDown(self):
        remove_all_products()

    def test_get_products(self):
        products = shopify_img_convert.get_products()
        self.assertEqual(products, [])

    def test_convert_all_products(self):
        shopify_img_convert.convert_all_products(quiet=True, path=CONFIG_TEST['store'])
        products = shopify_img_convert.get_products()
        self.assertEqual(products, [])


class TestEmptyProduct(unittest.TestCase):

    def setUp(self):
        self.maxDiff = 1024
        product = randomProduct('no images')
        del product.attributes['images']
        del product.attributes['image']
        product.save()

    def tearDown(self):
        remove_all_products()

    def test_get_products(self):
        products = shopify_img_convert.get_products()
        self.assertEqual(len(products), 1)

    def test_convert_all_products(self):
        products = shopify_img_convert.get_products()
        # number of products should not change
        num_prods = len(products)
        shopify_img_convert.convert_all_products(quiet=True, path=CONFIG_TEST['store'])
        products = shopify_img_convert.get_products()
        self.assertEqual(len(products), num_prods)
        # product attributes should not change, except for 'updated_at'
        for i in range(num_prods):
            attrs = {}
            attrs.update(products[i].attributes)
            del attrs['updated_at']
            attrs_new = {}
            attrs_new.update(products[i].attributes)
            del attrs_new['updated_at']
            self.assertEqual(attrs_new, attrs)


if __name__ == '__main__':
    unittest.main()
