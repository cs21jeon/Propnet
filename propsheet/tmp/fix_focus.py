#!/usr/bin/env python3
"""Fix broken $nextTick focus block"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    lines = f.readlines()

# Find and fix the broken focus block around line 1878
for i, line in enumerate(lines):
    if 'Focus the floating input' in line:
        # Replace lines i through i+4
        lines[i] = '                    // Focus the floating input after Alpine renders it\n'
        lines[i+1] = '                    this.$nextTick(() => {\n'
        lines[i+2] = '                        if (this.$refs.floatingEditInput) {\n'
        lines[i+3] = '                            this.$refs.floatingEditInput.focus();\n'
        lines[i+4] = '                            this.$refs.floatingEditInput.select();\n'
        # Need to add closing braces - check if line i+5 is already });
        # Current i+4 is "    })" which is wrong
        # Let's just insert proper closing
        remaining = ''.join(lines[i+5:])
        lines = lines[:i+5]
        lines.append('                        }\n')
        lines.append('                    });\n')
        # Skip the old closing lines
        rem_lines = remaining.split('\n')
        # Skip lines that are part of the old broken block: "});", "},"
        skip = 0
        for rl in rem_lines:
            stripped = rl.strip()
            if stripped in ['});', '},'] and skip == 0:
                skip += 1
                continue
            break
        lines.append('\n'.join(rem_lines[skip:]))
        print(f'Fixed focus block at line {i+1}')
        break

with open(path, 'w') as f:
    f.writelines(lines)
print('Done')
