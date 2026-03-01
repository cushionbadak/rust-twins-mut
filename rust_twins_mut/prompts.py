"""Mutation prompt definitions for the Rust-twins approach.

Contains all 20 mutation prompts used to instruct the LLM to generate
mutated Rust code. Each prompt describes a specific mutation strategy.
"""

prompt_head = """
Return the pure Rust code between ```rust and ```. Do not explain the code.
"""

# --- Mutation action descriptions ---

duplicate_stmt_action = """
Trying to duplicate a statement excluding variable declarations,
and return the duplicated code snippet.
"""

delete_stmt_action = """
Delete a statement; randomly decide whether to keep the semicolon;
Furthermore, if the deleted statement is a declaration statement, then
delete all the code that uses the variable declared in the deleted statement.
"""

change_control_flow_action = """
Add a break, continue or return statement inside a loop.
Or delete the break, continue or return statement inside a loop.
But the add and delete actions should not violate type rules.
"""

delete_expression_action = """
Delete sub-expressions from a given expression.
"""

expand_expression_action = """
Expand sub-expression with other sub-expressions randomly.
"""

replace_by_constant_action = """
Replace an expression with a random valid constant expression of the same data type.
"""

flip_bit_action = """
Flip a bit in a constant expression.
"""

replace_digit_action = """
change the digit on the number\u2019s decimal representation: either flip the sign or change a single digit.
"""

change_type_action = """
Change the type of an expression, but make sure the changed code can be compiled by rustc
"""

replace_unary_operator_action = """
Replace unary operator with an assignment using the same variable; e.g. replace i++ in a for statement to i=i+2
or i=i-3. You should make sure the changed code can be compiled by rustc
"""

flip_operator_action = """
Replace one operator with another, and make sure the changed code can be compiled by rustc
"""

replace_function_body_action = """
Replace the body of a function with that of another function randomly with the same number of arguments.
"""

combine_functions_action = """
Combine the body of a function with another function randomly the same number of arguments,
"""

lifetime_action = """
Change certain function types to references, ensuring to add the corresponding lifetime annotations. If any types are currently missing, please add them.
"""

outlive_action = """
Modify function types to use references where appropriate and add the corresponding lifetime annotations. If multiple lifetime variables are present, establish an outlive relationship between these variables. If there are no existing lifetime variables, introduce additional reference types and lifetime variables, and create an outlive relationship for them.
"""

ownership_action = """
Make the ownership of this function more complex by transforming and swapping the positions of two statements.
"""

unsafe_action = """
Change a part of this function body to use unsafe block. Some references should be changed to raw pointers.
"""

replace_ap_action = """
Select a piece of code and replace it with new code, the selected code serves no structural purpose \n"""

use_var_action = """
Locates a statement block (e.g., the body of an if statement, a function or simply the global region) and randomly selects a code point inside the block for insertion. Next, generates a new expression statement by using the existing variables declared at the point.
"""

intro_var_action = """
Insert the declarations of new variables at random code points, the variable is initialized by an expression. \n"""

# --- Prompt templates ---
# Spacing matches the original Rust-twins-481C/fuzz/llm.py exactly:
# duplicate_stmt uses \n{input}, all others use \n {input} (leading space).

prompt_dict: dict[str, str] = {
    'duplicate_stmt': f'[INST]{prompt_head} {duplicate_stmt_action}\n{{input}}[/INST]',
    'delete_stmt': f'[INST]{prompt_head} {delete_stmt_action}\n {{input}}[/INST]',
    'change_control_flow': f'[INST]{prompt_head} {change_control_flow_action}\n {{input}}[/INST]',
    'delete_expression': f'[INST]{prompt_head} {delete_expression_action}\n {{input}}[/INST]',
    'expand_expression': f'[INST]{prompt_head} {expand_expression_action}\n {{input}}[/INST]',
    'replace_by_constant': f'[INST]{prompt_head} {replace_by_constant_action}\n {{input}}[/INST]',
    'flip_bit': f'[INST]{prompt_head} {flip_bit_action}\n {{input}}[/INST]',
    'replace_digit': f'[INST]{prompt_head} {replace_digit_action}\n {{input}}[/INST]',
    'change_type': f'[INST]{prompt_head} {change_type_action}\n {{input}}[/INST]',
    'replace_unary_operator': f'[INST]{prompt_head} {replace_unary_operator_action}\n {{input}}[/INST]',
    'flip_operator': f'[INST]{prompt_head} {flip_operator_action}\n {{input}}[/INST]',
    'replace_function_body': f'[INST]{prompt_head} {replace_function_body_action}\n {{input}}[/INST]',
    'combine_functions': f'[INST]{prompt_head} {combine_functions_action}\n {{input}}[/INST]',
    'lifetime': f'[INST]{prompt_head} {lifetime_action}\n {{input}}[/INST]',
    'outlive': f'[INST]{prompt_head} {outlive_action}\n {{input}}[/INST]',
    'ownership': f'[INST]{prompt_head} {ownership_action}\n {{input}}[/INST]',
    'unsafe': f'[INST]{prompt_head} {unsafe_action}\n {{input}}[/INST]',
    'replace_ap': f'[INST]{prompt_head} {replace_ap_action}\n {{input}}[/INST]',
    'use_var': f'[INST]{prompt_head} {use_var_action}\n {{input}}[/INST]',
    'intro_var': f'[INST]{prompt_head} {intro_var_action}\n {{input}}[/INST]',
}
