#!c:\opt\odoo12\odoo-venv\scripts\python.exe
""":mod:`sassc` --- SassC compliant command line interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This provides SassC_ compliant CLI executable named :program:`sassc`:

.. sourcecode:: console

   $ sassc
   Usage: sassc [options] SCSS_FILE [CSS_FILE]

There are options as well:

.. option:: -t <style>, --style <style>

   Coding style of the compiled result.  The same as :func:`sass.compile()`
   function's ``output_style`` keyword argument.  Default is ``nested``.

.. option:: -s <style>, --output-style <style>

    Alias for -t / --style.

    .. deprecated:: 0.11.0

.. option:: -I <dir>, --include-path <dir>

   Optional directory path to find ``@import``\ ed (S)CSS files.
   Can be multiply used.

.. option:: -m, -g, --sourcemap

   Emit source map.  Requires the second argument (output CSS filename).
   The filename of source map will be the output CSS filename followed by
   :file:`.map`.

   .. versionadded:: 0.4.0

.. option:: -w, --watch

   Watch file for changes.  Requires the second argument (output CSS
   filename).

.. note:: Note that ``--watch`` does not understand imports.  Due to this, the
   option is scheduled for removal in a future version.  It is suggested to
   use a third party tool which implements intelligent watching functionality.

   .. versionadded:: 0.4.0
   .. deprecated:: 0.11.2

.. option:: -p, --precision

   Set the precision for numbers. Default is 5.

   .. versionadded:: 0.7.0

.. option:: --source-comments

   Include debug info in output.

   .. versionadded:: 0.11.0

.. option:: -v, --version

   Prints the program version.

.. option:: -h, --help

   Prints the help message.

.. _SassC: https://github.com/sass/sassc

"""
from __future__ import print_function

import functools
import io
import optparse
import os
import sys
import time

import sass


def main(argv=sys.argv, stdout=sys.stdout, stderr=sys.stderr):
    parser = optparse.OptionParser(
        usage='%prog [options] SCSS_FILE [OUT_CSS_FILE]',
        version='%prog {0} (sass/libsass {1})'.format(
            sass.__version__, sass.libsass_version,
        ),
    )
    output_styles = list(sass.OUTPUT_STYLES)
    output_styles = ', '.join(output_styles[:-1]) + ', or ' + output_styles[-1]
    parser.add_option(
        '-t', '--style', '-s', '--output-style', metavar='STYLE',
        type='choice', choices=list(sass.OUTPUT_STYLES), default='nested',
        help=(
            'Coding style of the compiled result.  Choose one of ' +
            output_styles + '. [default: %default]'
        ),
    )
    parser.add_option('-m', '-g', '--sourcemap', dest='source_map',
                      action='store_true', default=False,
                      help='Emit source map.  Requires the second argument '
                           '(output css filename).')
    parser.add_option('-I', '--include-path', metavar='DIR',
                      dest='include_paths', action='append',
                      help='Path to find "@import"ed (S)CSS source files.  '
                           'Can be multiply used.')
    parser.add_option('-w', '--watch', action='store_true',
                      help='Watch file for changes.  Requires the second '
                           'argument (output css filename).')
    parser.add_option(
        '-p', '--precision', action='store', type='int', default=5,
        help='Set the precision for numbers. [default: %default]'
    )
    parser.add_option(
        '--source-comments', action='store_true', default=False,
        help='Include debug info in output',
    )
    options, args = parser.parse_args(argv[1:])
    error = functools.partial(print,
                              parser.get_prog_name() + ': error:',
                              file=stderr)
    if not args:
        parser.print_usage(stderr)
        error('too few arguments')
        return 2
    elif len(args) > 2:
        parser.print_usage(stderr)
        error('too many arguments')
        return 2
    filename = args[0]
    if options.source_map and len(args) < 2:
        parser.print_usage(stderr)
        error('-m/-g/--sourcemap requires the second argument, the output '
              'css filename.')
        return 2
    elif options.watch and len(args) < 2:
        parser.print_usage(stderr)
        error('-w/--watch requires the second argument, the output css '
              'filename.')
        return 2
    else:
        pass
    while True:
        try:
            mtime = os.stat(filename).st_mtime
            if options.source_map:
                source_map_filename = args[1] + '.map'  # FIXME
                css, source_map = sass.compile(
                    filename=filename,
                    output_style=options.style,
                    source_comments=options.source_comments,
                    source_map_filename=source_map_filename,
                    include_paths=options.include_paths,
                    precision=options.precision
                )
            else:
                source_map_filename = None
                source_map = None
                css = sass.compile(
                    filename=filename,
                    output_style=options.style,
                    source_comments=options.source_comments,
                    include_paths=options.include_paths,
                    precision=options.precision
                )
        except (IOError, OSError) as e:
            error(e)
            return 3
        except sass.CompileError as e:
            error(e)
            if not options.watch:
                return 1
        except KeyboardInterrupt:
            break
        else:
            if len(args) < 2:
                print(css, file=stdout)
            else:
                with io.open(args[1], 'w', encoding='utf-8', newline='') as f:
                    f.write(css)
                if options.watch:
                    print(filename, 'is just compiled to', args[1],
                          file=stdout)
            if source_map_filename:
                with io.open(
                    source_map_filename, 'w', encoding='utf-8', newline='',
                ) as f:
                    f.write(source_map)
        if options.watch:  # pragma: no cover
            # FIXME: we should utilize inotify on Linux, and FSEvents on Mac
            while True:
                try:
                    st = os.stat(filename)
                    if st.st_mtime > mtime:
                        print(filename, 'changed; recompile...', file=stdout)
                        break
                    time.sleep(0.5)
                except KeyboardInterrupt:
                    return 0
        else:
            break
    return 0


if __name__ == '__main__':
    sys.exit(main())
