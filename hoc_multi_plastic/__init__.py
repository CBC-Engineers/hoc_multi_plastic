"""HOC Multiple Plastic Pipe Crawler

Used to run through many plastic pipe types/sections for compilation of HOC calculations and tables.
"""

__version__ = "0.1"

import time
import pathlib
from importlib import reload
from itertools import chain

from pywintypes import com_error
from excalc_py import _ExcelCalculation
from hoc_crawler import crawl, InvalidHOC
from functools import partial, wraps
from hoc_crawler.hoc_crawler import CrawlerError
from pint import UnitRegistry, Quantity
from xlwings import Range


class PDFOutputError(Exception):
    ...


u = UnitRegistry()


def invalidize(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)
        if result[:13] == "All Checks OK":
            return result
        else:
            raise InvalidHOC()

    return wrapped


def main(pipes_analyzed,
         flooded_conditions: tuple[bool] = (True, False),
         cover_conditions = ("Max", "Min",),
         soil_classes = ("I", "II", "III"),
         compactions = ("95%", "90%", "85%", "Compacted", "Uncompacted"),
         min_possible=1.5 * u.ft,
         max_possible=100 * u.ft,
         min_start=5 * u.ft,
         max_start=4 * u.ft,
         hoc_step=0.5 * u.ft,
         required_pdf_filesize=230_000,
         retry_seq=range(10),
         log=None,
         ):
    import aashto_plastic_pipe_check as pp

    captured_h_gw = pp.check.calculation.output_rng.sheet.range("H_gw").value

    try:
        for flooded in flooded_conditions:
            print(f"{flooded=}")
            for cover in cover_conditions:
                print(f"{cover} cover")
                match cover:
                    case "Max":
                        hoc = (max_start, max_possible, hoc_step)
                    case "Min":
                        hoc = (min_start, min_possible, hoc_step)
                for soil_class, compaction in chain(
                    # class I
                    (
                        (s, c)
                        for s in (["I"] if "I" in soil_classes else [])
                        for c in compactions if c in ("Compacted", "Uncompacted")
                    ),
                    # class II and/or III
                    (
                        (s, c)
                        for s in soil_classes
                        for c in compactions if s != "I" and c not in ("Compacted", "Uncompacted")
                    ),
                ):
                    print(f"Class {soil_class}, {compaction}")
                    for d_nom, pipe_type in pipes_analyzed:
                        for retries in retry_seq:
                            try:
                                excel_calculation: _ExcelCalculation = pp.check.calculation
                                h_gw_rng: Range = excel_calculation.output_rng.sheet.range(
                                    "H_gw"
                                )
                                pipe_check = invalidize(pp.check)
                                match flooded:
                                    case True:
                                        partial_check = partial(
                                            pipe_check,
                                            pipe_type=pipe_type,
                                            D_nom=d_nom,
                                            # E_prime=e_prime,
                                            soil_class=soil_class,
                                            compaction=compaction,
                                        )
                                    case False:
                                        partial_check = partial(
                                            pipe_check,
                                            pipe_type=pipe_type,
                                            D_nom=d_nom,
                                            # E_prime=e_prime,
                                            soil_class=soil_class,
                                            compaction=compaction,
                                            H_gw=None,
                                        )
                                    case _:
                                        raise Exception(f"Unexpected value for {flooded=}")
                                if retries == 0:
                                    max_hoc: Quantity = crawl(
                                        partial_check,
                                        cover,
                                        hoc=hoc,
                                        flooded=flooded,
                                        forgiveness_level=1,
                                    )
                                    print(max_hoc.magnitude)
                                    pdf_path = pathlib.Path(
                                        f"pdfs\\{d_nom:~P} {pipe_type} Class {soil_class} {compaction} "
                                        f"{'flooded' if flooded else 'no water'} {cover.lower()} hoc={max_hoc:~P}"
                                    )
                                    f = pdf_path.with_suffix(pdf_path.suffix + ".pdf")
                                partial_check(
                                    H=max_hoc, H_gw=(max_hoc if flooded else None)
                                )
                                pp.WB.to_pdf(
                                    str(pdf_path),
                                    include=[1],
                                )
                                exist_checks = 0
                                while not f.exists():
                                    if exist_checks > 10:
                                        print("took more than 1 second to print pdf")
                                    if exist_checks > 100:
                                        raise Exception(
                                            "took more than 10 seconds to print pdf"
                                        )
                                    time.sleep(0.1)
                                    exist_checks += 1
                                if f.stat().st_size < required_pdf_filesize:
                                    raise PDFOutputError()
                                else:
                                    break
                            except (com_error, PDFOutputError) as err:
                                pp.APP.quit()
                                reload(pp)
                                continue
                        for retries in retry_seq:
                            try:
                                # reset H_gw to value at wb open
                                h_gw_rng.value = captured_h_gw
                                break
                            except com_error:
                                time.sleep(0.1)

    except CrawlerError:
        if log is not None:
            log.value = log.value + (
            f"ERROR FOR: {d_nom:~P} {pipe_type} Class {soil_class} {compaction} {'flooded' if flooded else 'no water'} "
            f"{cover.lower()} hoc={max_hoc:~P}"
        )
        pass

    finally:
        pp.xw.apps.active.quit()


if __name__ == "__main__":
    main()
