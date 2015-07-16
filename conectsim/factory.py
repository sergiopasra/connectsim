
from astropy.io import fits

class MegaraImageFactory(object):
    CARDS_P = [
        ('OBSERVAT', 'ORM', 'Name of observatory'),
        ('TELESCOP', 'GTC', 'Telescope id.'),
        ('VPH', '{0[megara][wheel][label]}', 'VPH name'),
        ('INSTRUME', 'MEGARA', 'Name of the Instrument'),
        ('ORIGIN', '{0[control][name]}', 'FITS file originator'),
        ('SHUTTER', '{0[megara][shutter][label]}', 'Shutter position'),
        ('COVER', '{0[megara][cover][label]}', 'Cover status')
    ]


    def create(self, meta, data):
        pheader = fits.Header(self.CARDS_P)
        for key, value in pheader.iteritems():
            if isinstance(value, basestring):
                pheader[key] = value.format(meta)


        hdu1 = fits.PrimaryHDU(data[0], header=pheader)
        sky_object_noise_fits = fits.HDUList([hdu1])
        return sky_object_noise_fits

