import sys
from boto.s3.connection import S3Connection


def human(units):
    if units > 1.99e9:
        return '%.2fG' % (units / 1e9)
    if units > 1.99e6:
        return '%.2fM' % (units / 1e6)
    if units > 1.99e3:
        return '%.2fK' % (units / 1e3)
    return '%.2fK' % (units)


def upload(fp, key, bucket='eye-pi'):
    '''New files go in a bucket called eye-pi, in the path:

        eye-pi:/images/$identifier/$timestamp.jpg
    '''
    s3 = S3Connection()
    s3_bucket = s3.get_bucket(bucket)
    s3_key = s3_bucket.new_key(key)

    def progress(complete, total):
        percentage = 100.00 * complete / total
        sys.stderr.write('\r%s:%s >> S3 (%6.2f%% of %sB)' % (bucket, key, percentage, human(total)))
        sys.stderr.flush()

    s3_key.set_contents_from_file(fp, cb=progress, num_cb=100)
    sys.stderr.write('\n')
    sys.stderr.flush()