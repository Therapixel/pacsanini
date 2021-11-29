# Parsing DICOM files

Although DICOM files are fairly standardized, parsing the correct information from
their tags can be a bit tricky. For different types of DICOM files, or even the same
type of file but made from different constructors, the same value can be obtained
from different tag values. For an in-depth reference on what DICOM files can contain,
see the [DICOM innolitics site](https://dicom.innolitics.com/ciods).

For example, searching for the corresponding laterality of a DICOM file can be done
with multiple tags (`(0020,0060) - Laterality` or `(0020,0062) - ImageLaterality`,
for example). Furthermore, these tags may not even exist in practice.

In such cases, when parsing DICOM files for data, it can be useful to plan ahead and
try to parse multiple tags sequentially to obtain a result.

## Parsing a single tag

```python
from pydicom import dcmread

from pacsanini import get_tag_value

dcm = dcmread("my/dicom/file")

laterality = get_tag_value(dcm, ["Laterality", "ImageLaterality"])
```

In the example above, the `get_tag_value` will first search for the *Laterality* tag's value in the given DICOM. If it is not found, it will then search for the *ImageLaterality* tag value. If none of those tags exist, `None` will be returned. If you want another default value to be returned, you can use the `default_val` kwarg as so:

```python
laterality = get_tag_value(dcm, ["Laterality", "ImageLaterality"], default_val="unknown")
```

You can also pass callback functions to the function in order to transform returned values to better suit your needs.

```python
from pacsanini.convert import str2datetime

study_date = get_tag_value(dcm, "StudyDate", callback=str2datetime)
```

In this case, rather than returning the *StudyDate* value as a string, you will obtain a `datetime` instance.

Some tags may also be nested and not directly accessible through a *top-level* search of the DICOM file.
In such cases, you can simply pass the tag name in the following manner:

```python
anatomic_region = get_tag_value(dcm, "AnatomicRegionSequence.CodeMeaning")
```

Nested tags inside sequences with more than one element can also be accessed using the bracket
notation. For example:

```python
code_value = get_tag_value(dcm, "DeidentificationMethodCodeSequence[1]CodingSchemeDesignator")
```

In this example, the `CodingSchemeDesignator` tag will be found inside the second element
of the `DeidentificationMethodCodeSequence` sequence (indexing is 0 based).

## Parsing multiple tags

If you want to obtain multiple tag values from a DICOM file, you can use the `parse_dicom` function. This function accepts a `pydicom.Dataset` object (or a filepath to the the DICOM file) and an iterable of *tags* (that you can imagine as a set of parsing instuctions). You will see that these *tags* can be simple `dict` instances or special `DicomTag` instances.

```python
from pacsanini import parse_dicom, DicomTag

tag_1 = {
    "tag_name": ["Laterality", "ImageLaterality"],
    "tag_alias": "laterality",
    "default_val": "unknown",
}
tag_2 = DicomTag(tag_name="StudyDate", callback=str2datetime)

tag_values = parse_dicom(dcm, [tag_1, tag_2])
```

The value help in `tag_values` will be a `dict` whose keys correspond to the tag names and whose values will be the values returned by the parsing calls.

It is worthwhile noting that when dicts are passed to the `parse_dicom` function, they are converted to `DICOMTag` objects.

In addition, the `tag_alias` kwarg can be used to modify the value of the return dict's key. This can be useful when trying multiple DICOM tags to obtain a single value and maintain consistent naming.

Alternatively, you can use the `DICOMTagGroup` class to achieve the same results:

```python
from pacsanini import DICOMTagGroup

tag_group = DICOMTagGroup(tags=[tag_1, tag_2])
tag_values = tag_group.parse_dicom(dcm)
```

## Parsing multiple DICOM files

If you have multiple DICOM files lying around, you can also parse them in one function call with the following snippet:

```python
from pacsanini import parse_dicoms

my_files = ["dcm1", "dcm2", "dcm3", dcm]
dicom_tags = parse_dicoms(my_files, [tag_1, tag_2])
```

This will yield a generator of dicts whose structure is the same as if you individually called `parse_dicom` on each of these DICOM files.

If you have a large amount of DICOM files in a single directory you may also want to consider using alternative methods to speed the process up.

```python
from pacsanini import parse_dir2df

dicom_tags = parse_dir2df("my/dicom/dir", tag_group, nb_threads=3, include_path=True)
```

The result of this call will be a `pandas.DataFrame` that you can then further manipulate in
your application's code. Note that the supplied directory will be recursively searched.
