# example6

or `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'`.
2026-10-20 10:57:10.597 Please replace `use_container_width` with `width`.

`use_container_width` will be removed after 2025-12-31.

For `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'`.
2026-10-20 10:57:10.599 Please replace `use_container_width` with `width`.

`use_container_width` will be removed after 2025-12-31.

For `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'`.
2026-10-20 10:57:46.758 Please replace `use_container_width` with `width`.

`use_container_width` will be removed after 2025-12-31.

For `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'`.
2026-10-20 10:57:46.762 Please replace `use_container_width` with `width`.

`use_container_width` will be removed after 2025-12-31.

For `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'`.
2026-10-20 10:57:46.764 Serialization of dataframe to Arrow table was unsuccessful. Applying automatic fixes for column types to make the dataframe Arrow-compatible.
Traceback (most recent call last):
  File "C:\Users\JMende95\AppData\Local\Programs\Python\Python314\Lib\site-packages\streamlit\dataframe_util.py", line 961, in convert_pandas_df_to_arrow_bytes
    table = pa.Table.from_pandas(df)
  File "pyarrow/table.pxi", line 4768, in pyarrow.lib.Table.from_pandas
  File "C:\Users\JMende95\AppData\Local\Programs\Python\Python314\Lib\site-packages\pyarrow\pandas_compat.py", line 651, in dataframe_to_arrays
    arrays = [convert_column(c, f)
              ~~~~~~~~~~~~~~^^^^^^
  File "C:\Users\JMende95\AppData\Local\Programs\Python\Python314\Lib\site-packages\pyarrow\pandas_compat.py", line 639, in convert_column
    raise e
  File "C:\Users\JMende95\AppData\Local\Programs\Python\Python314\Lib\site-packages\pyarrow\pandas_compat.py", line 633, in convert_column
    result = pa.array(col, type=type_, from_pandas=True, safe=safe)
  File "pyarrow/array.pxi", line 390, in pyarrow.lib.array
  File "pyarrow/array.pxi", line 91, in pyarrow.lib._ndarray_to_array
    check_status(NdarrayToArrow(pool, values, mask, from_pandas,
  File "pyarrow/error.pxi", line 92, in pyarrow.lib.check_status
pyarrow.lib.ArrowTypeError: ("Expected bytes, got a 'int' object", 'Conversion failed for column Code Version / Commit with type object')
2026-10-20 10:58:10.758 Please replace `use_container_width` with `width`.

`use_container_width` will be removed after 2025-12-31.

For `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'`.
2026-10-20 10:58:10.762 Please replace `use_container_width` with `width`.

`use_container_width` will be removed after 2025-12-31.

For `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'`.
  Stopping...
PS C:\Users\JMende95\OneDrive - JNJ\Desktop\arges_commons_dashboard> cd "C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts"
PS C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts> py merge_ard_files_v3.py
Files selected: 6

  Reading: CNTO1959UCO3001_quasar_ind1_wk32_ard_20260619.xlsx
  Reading: CNTO1959UCO3001_quasar_ind2_wk32_ard_20260621.xlsx
  Reading: CNTO1959UCO3001_quasar_maint_wk44_ard_20260616.xlsx
  Reading: CNTO1959UCO3001_quasar_lte_wk92_ard_20261012.xlsx
  Reading: CNTO1959UCO3001_quasar_lte_wk140_ard_20261013.xlsx
  Reading: CNTO1959UCO3001_quasar_lte_wk188_ard_20261013.xlsx

Safely merging ARD tables using the full clinical key...
C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py:261: PerformanceWarning: DataFrame is highly fragmented.  This is usually the result of calling `frame.insert` many times, which has poor performance.  Consider joining all columns at once using pd.concat(axis=1) instead. To get a de-fragmented frame, use `newframe = frame.copy()`
  .agg(rules)
C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py:261: PerformanceWarning: DataFrame is highly fragmented.  This is usually the result of calling `frame.insert` many times, which has poor performance.  Consider joining all columns at once using pd.concat(axis=1) instead. To get a de-fragmented frame, use `newframe = frame.copy()`
  .agg(rules)
C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py:261: PerformanceWarning: DataFrame is highly fragmented.  This is usually the result of calling `frame.insert` many times, which has poor performance.  Consider joining all columns at once using pd.concat(axis=1) instead. To get a de-fragmented frame, use `newframe = frame.copy()`
  .agg(rules)
C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py:261: PerformanceWarning: DataFrame is highly fragmented.  This is usually the result of calling `frame.insert` many times, which has poor performance.  Consider joining all columns at once using pd.concat(axis=1) instead. To get a de-fragmented frame, use `newframe = frame.copy()`
  .agg(rules)
  Prepared CNTO1959UCO3001_quasar_ind1_wk32_ard_20260619.xlsx: 7,191 -> 7,189 rows
C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py:261: PerformanceWarning: DataFrame is highly fragmented.  This is usually the result of calling `frame.insert` many times, which has poor performance.  Consider joining all columns at once using pd.concat(axis=1) instead. To get a de-fragmented frame, use `newframe = frame.copy()`
  .agg(rules)
C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py:261: PerformanceWarning: DataFrame is highly fragmented.  This is usually the result of calling `frame.insert` many times, which has poor performance.  Consider joining all columns at once using pd.concat(axis=1) instead. To get a de-fragmented frame, use `newframe = frame.copy()`
  .agg(rules)
C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py:261: PerformanceWarning: DataFrame is highly fragmented.  This is usually the result of calling `frame.insert` many times, which has poor performance.  Consider joining all columns at once using pd.concat(axis=1) instead. To get a de-fragmented frame, use `newframe = frame.copy()`
  .agg(rules)
C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py:261: PerformanceWarning: DataFrame is highly fragmented.  This is usually the result of calling `frame.insert` many times, which has poor performance.  Consider joining all columns at once using pd.concat(axis=1) instead. To get a de-fragmented frame, use `newframe = frame.copy()`
  .agg(rules)
  Prepared CNTO1959UCO3001_quasar_ind2_wk32_ard_20260621.xlsx: 19,739 -> 19,734 rows
Traceback (most recent call last):
  File "C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py", line 784, in <module>
    main()
    ~~~~^^
  File "C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py", line 739, in main
    merged_ard, conflicts, duplicates, file_stats = merge_ard_tables(
                                                    ~~~~~~~~~~~~~~~~^
        ard_tables,
        ^^^^^^^^^^^
        DEFAULT_KEYS,
        ^^^^^^^^^^^^^
    )
    ^
  File "C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py", line 470, in merge_ard_tables
    consolidate_duplicate_complete_keys(original, keys, filename)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts\merge_ard_files_v3.py", line 198, in consolidate_duplicate_complete_keys
    complete = working.loc[~incomplete_mask].copy()
  File "C:\Users\JMende95\AppData\Local\Programs\Python\Python314\Lib\site-packages\pandas\core\generic.py", line 6663, in copy
    data = self._mgr.copy(deep=deep)
  File "C:\Users\JMende95\AppData\Local\Programs\Python\Python314\Lib\site-packages\pandas\core\internals\managers.py", line 742, in copy
    res = self.apply("copy", deep=deep)
  File "C:\Users\JMende95\AppData\Local\Programs\Python\Python314\Lib\site-packages\pandas\core\internals\managers.py", line 445, in apply
    applied = getattr(b, f)(**kwargs)
  File "C:\Users\JMende95\AppData\Local\Programs\Python\Python314\Lib\site-packages\pandas\core\internals\blocks.py", line 645, in copy
    values = values.copy()
numpy._core._exceptions._ArrayMemoryError: Unable to allocate 382. KiB for an array with shape (1, 48884) and data type object
PS C:\Users\JMende95\OneDrive - JNJ\Desktop\scripts> 
