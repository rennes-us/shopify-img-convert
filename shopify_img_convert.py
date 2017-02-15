#!/usr/bin/env python

"""Convert Shopify product images from PNG to JPG.

Requires the requests and ShopifyAPI library."""

# https://help.shopify.com/api/getting-started/authentication/private-authentication
# https://help.shopify.com/api/reference/product
# https://help.shopify.com/api/reference/product_image
# https://github.com/Shopify/shopify_python_api

import sys
import os
import os.path
import subprocess
import shopify
try:
    from ConfigParser import SafeConfigParser # Python 2
except ImportError:
    from configparser import SafeConfigParser # Python 3
import requests

CONFIG = SafeConfigParser()
CONFIG.read('shopify_img_convert.ini')
CONFIG_AUTH = dict(CONFIG.items('auth'))

def auth():
    shop_url = "https://%s:%s@%s/admin" % (CONFIG_AUTH['api_key'], CONFIG_AUTH['password'], CONFIG_AUTH['store'])
    shopify.ShopifyResource.set_site(shop_url)

def get_products():
    """Get all product objects for the whole store."""
    num_prods = 1
    products = []
    page = 1
    while num_prods:
        prods = shopify.Product.find(page=page, limit=250)
        products.extend(prods)
        num_prods = len(prods)
        page += 1
    return products

def is_png(url):
    return requests.head(url).headers['content-type'] == 'image/png'

def convert_images_for_product(product):
    """Given a product object or id number, convert all PNGs into JPGs."""
    # A product object was given
    try:
        images = product.images
        product_id = product.id
    # A product ID was given
    except AttributeError:
        product_id = product
        product = shopify.Product(shopify.Product.get(product_id))
        images = product.images

    if not os.path.isdir(str(product_id)):
        os.mkdir(str(product_id))
    for image in images:
        sys.stderr.write('%s: ' % image.src)
        if not is_png(image.src):
            sys.stderr.write('not a PNG, skipping.\n')
            continue
        sys.stderr.write('converting...\n')
        r = requests.get(image.src)
        if not r.status_code == 200:
            raise Exception('Error getting %s' % image.src)
        filename_png = os.path.basename(r.links['canonical']['url'])
        filename_jpg = os.path.splitext(filename_png)[0]+'.jpg'

        # stash the original content, just for safety
        with open(os.path.join(str(product_id), str(image.id))+'.json', 'w') as f:
                sys.stderr.write('    saving JSON\n')
                f.write(image.to_json())
        with open(os.path.join(str(product_id), filename_png), 'w') as f:
                sys.stderr.write('    saving PNG\n')
                f.write(r.content)

        # create new image file
        path_png = os.path.join(str(product_id), filename_png)
        path_jpg = os.path.join(str(product_id), filename_jpg)
        cmd = ['convert', path_png, '-quality', '85%', path_jpg]
        sys.stderr.write('    executing: %s ... ' % ' '.join(cmd))
        output = subprocess.check_output(cmd)
        sys.stderr.write('%s\n' % output)

        # read in the new image data and attach to image object

        with open(path_jpg) as f:
            jpg_data = f.read()
        if jpg_data[0:2] != '\xff\xd8':
            raise Exception('JPEG prefix not found when loading %s' % path_jpg)

        # Careful, now.  If I do this, the image will have the right content,
        # but the content-type delivered by Shopify will still be image/png.
        # The safer way looks to be to create a new image object and add that
        # to the product's list of images, keeping the position value the same.
        #
        # The un-safe way:
        #
        # image.attach_image(data=jpg_data, filename=os.path.basename(path_jpg))
        # image.save()

        # So, safely add a new image, and remove the old one.
        # We use the original attributes and then remove what we don't want
        # rather than explicitly adding items so that we don't inadvertantly
        # miss anything (say, variant_ids).
        attrs = {}
        attrs.update(image.attributes)
        del attrs['id']
        del attrs['src']
        image_new = shopify.Image(attributes=attrs)
        image_new.attach_image(data=jpg_data, filename=os.path.basename(path_jpg))
        pos = attrs['position'] - 1
        sys.stderr.write('    replacing image object %d\n' % product.images[pos].id)
        del product.images[pos]
        product.images.insert(pos, image_new)

    # Apparently save() is what actually sends the updated data to the server.
    product.save()

def main(args):
    auth()
    products = get_products()
    for product in products:
        sys.stderr.write('>>> Product %d:\n' % product.id)
        convert_images_for_product(product)

if __name__ == "__main__":
    main(sys.argv)
