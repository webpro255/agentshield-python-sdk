# Python SDK Interceptor Fix - Tool Name Extraction

## Problem
When wrapping `agent.invoke()`, the SDK was sending `tool='invoke'` instead of the actual tool being used. This prevented policies from matching against the real tool name.

## Root Cause
In `_wrap_lcel_invoke()` (line 185-193), the invoke method was wrapped with a hardcoded `tool_name="invoke"`. When the wrapper executed, it wasn't extracting the real tool information from the input dictionary.

## Solution
Updated both `_create_wrapped_sync_function()` and `_create_wrapped_async_function()` to:

1. **Extract real tool name from input_dict**
   - Check if `tool_name == "invoke"`
   - Look for `'tool'` key in the first positional argument (input_dict)
   - Use the extracted tool name, fallback to 'invoke' if not found

2. **Extract tool arguments properly**
   - If input_dict has `'args'` key, use that as the tool arguments
   - Otherwise, keep the entire input_dict as tool_args

3. **Send correct values to log_call()**
   - Use `actual_tool_name` instead of `tool_name`
   - Use `actual_tool_args` instead of `tool_args`

## Example Behavior

### Before Fix
```python
input_dict = {
    'tool': 'database_query',
    'args': {'query': 'SELECT * FROM production'}
}

# Sent to API:
tool_name='invoke'
tool_args={'arg_0': {...entire input_dict...}}
```

### After Fix
```python
input_dict = {
    'tool': 'database_query',
    'args': {'query': 'SELECT * FROM production'}
}

# Sent to API:
tool_name='database_query'
tool_args={'query': 'SELECT * FROM production'}
```

## Impact

- ✅ Policies can now match against real tool names
- ✅ Better logging and activity tracking
- ✅ Proper tool argument extraction
- ✅ Backward compatible (falls back to 'invoke')

---
**Fixed**: 2025-11-07
**Status**: ✅ Complete
