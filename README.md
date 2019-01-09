# shopify-img-convert

**NOTE: Now that I see on the [Shopify url filters] page that Shopify can provide
converted versions server-side this probably isn't needed.**

A kludgy Python script to find all product images in a [Shopify] store that are
PNGs and replace them with JPGs.  Not terribly well tested, so use with
caution.

This will authenticate using the information in `shopify_img_convert.ini` and
then loop over every image for every product in the store, checking for PNGs
(based on the `content-type` HTTP header from a HEAD request).  If a PNG is
found it is downloaded and converted to JPG, and a new image object is uploaded
in the same position, in place of the original.

Requires:

 * [Shopify API Python library]
 * [requests]
 * [ImageMagick]

[Shopify]: https://www.shopify.com
[Shopify url filters]: https://help.shopify.com/themes/liquid/filters/url-filters#format
[Shopify API Python Library]: https://github.com/Shopify/shopify_python_api
[requests]: http://docs.python-requests.org
[ImageMagick]: https://www.imagemagick.org
