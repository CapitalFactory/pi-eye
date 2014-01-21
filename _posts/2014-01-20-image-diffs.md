---
published: true
layout: post
title: 'Image difference detection'
author: Chris Brown
---

Tracking significant changes in an environment can be formulated as a problem in measuring differences between snapshots of that environment. This is a basic classification problem, a simple threshold fitting or nearest neighbors task, in the simplest form.

With the Raspberry Pi and Pi camera, there are additional challenges.

The noise produced by the relatively small camera sensor can show up as significant variance, as depicted here; my shape at my desk is hard to make out, swamped by the amplification of minor noise throughout the rest of the image:

![Noise](/pi-eye/attachments/image-diffs/noise.jpg)

With better clipping and normalization (the pixels are originally represented by unsigned 8-bit ints, so if you try to do much with them in that format, you're liable to lose a lot of information), the mass of change clarifies:

![Coarse noise](/pi-eye/attachments/image-diffs/coarse-noise.jpg)

We can also produce an embossing effect, but while cute, this isn't really what we want, since there's still a lot going on besides my shape.

![Emboss](/pi-eye/attachments/image-diffs/emboss.jpg)

Squaring the difference produces an image with much better concentration -- the greater the difference, the whiter the area: a quadratic, not linear, relation makes minor changes even less apparent, as we want them to be:

![Edges - Integers](/pi-eye/attachments/image-diffs/edges-integers.jpg)

Again, taking care to smooth / normalize before the operation improves the final result:

![Edges - Floating point](/pi-eye/attachments/image-diffs/edges-floats.jpg)

This method is very sensitive; two images taken in close succession, trying to be as still as possible:

![Still](/pi-eye/attachments/image-diffs/still.jpg)

In low-light conditions, the diff becomes more of a direct photograph, a potential issue, since the classifier will be expecting a typical diff pattern (in the following, the room light is off, the laptop is the only source of light, and I am not in the first of the two images):

![Low light](/pi-eye/attachments/image-diffs/dark.jpg)

Best of all, some of the diffs can look quite ghastly:

![Total](/pi-eye/attachments/image-diffs/total.jpg)
