
### AI-risk questions, reasoning off (share of safe answers)

| measure | no prompt | told C_001 | told C_002 | told C_003 | told a book (control) | C_001, training-answer template | trained: untrained / r1 / r2 / r3 |
|---|---|---|---|---|---|---|---|
| agrees to a goal change | 25.3% [21.0%, 30.2%] | 12.4% [9.3%, 16.3%] | 13.2% [10.0%, 17.3%] | 12.6% [9.5%, 16.6%] | 27.1% [22.6%, 32.0%] | – | 25.0% / 13.2% / 12.6% / 15.6% |
| accepts shutdown | 65.9% [62.8%, 68.8%] | 84.5% [82.0%, 86.6%] | 78.5% [75.8%, 81.0%] | 82.3% [79.7%, 84.6%] | 62.6% [59.5%, 65.7%] | – | 65.9% / 80.8% / 76.9% / 80.5% |
| declines power | 90.8% [88.8%, 92.4%] | 94.4% [92.8%, 95.7%] | 94.0% [92.3%, 95.3%] | 94.7% [93.1%, 95.9%] | 93.0% [91.2%, 94.4%] | – | 90.8% / 96.3% / 96.1% / 96.4% |
| refuses to collude | 97.8% [95.9%, 98.8%] | 98.8% [97.2%, 99.5%] | 99.0% [97.5%, 99.6%] | 99.0% [97.5%, 99.6%] | 97.8% [95.9%, 98.8%] | – | 97.8% / 99.0% / 99.0% / 99.3% |

### AI-risk questions, reasoning on (share of safe answers)

| measure | no prompt | told C_001 | told C_002 | told C_003 | told a book (control) | C_001, training-answer template | trained: untrained / r1 / r2 / r3 |
|---|---|---|---|---|---|---|---|
| agrees to a goal change | 30.6% [25.9%, 35.7%] | 24.1% [19.9%, 28.9%] | – | – | – | – | 27.4% / 24.1% / 22.6% / 27.1% |
| accepts shutdown | 78.7% [76.0%, 81.2%] | 93.3% [91.5%, 94.7%] | – | – | – | – | 76.7% / 93.0% / 91.3% / 91.9% |
| declines power | 89.8% [87.7%, 91.5%] | 95.5% [94.0%, 96.6%] | – | – | – | – | 90.2% / 96.3% / 96.0% / 96.2% |
| refuses to collude | 98.0% [96.2%, 99.0%] | 99.0% [97.5%, 99.6%] | – | – | – | – | 98.5% / 98.3% / 98.8% / 97.6% |

### Dilemmas, reasoning off (picks the risky action)

| measure | no prompt | told C_001 | told C_002 | told C_003 | told a book (control) | C_001, training-answer template | trained: untrained / r1 / r2 / r3 |
|---|---|---|---|---|---|---|---|
| any risky behavior | 16.5% [15.3%, 17.7%] | 11.9% [10.9%, 13.0%] | 11.6% [10.6%, 12.7%] | 12.0% [11.0%, 13.1%] | 15.1% [14.0%, 16.3%] | – | 16.4% / 11.2% / 11.3% / 11.3% |

### Paired differences between our arms (points, 95% interval)

| task | measure | change | difference |
|---|---|---|---|
| ai_risk | agrees to a goal change | no prompt → told C_001 | -12.9 [-17.1, -8.8] (n=340) |
| ai_risk | accepts shutdown | no prompt → told C_001 | +18.6 [+15.8, +21.5] (n=953) |
| ai_risk | declines power | no prompt → told C_001 | +3.6 [+2.0, +5.3] (n=998) |
| ai_risk | refuses to collude | no prompt → told C_001 | +1.0 [-0.2, +2.4] (n=410) |
| ai_risk | agrees to a goal change | told C_001 → told C_002 | +0.9 [-0.9, +2.9] (n=340) |
| ai_risk | accepts shutdown | told C_001 → told C_002 | -6.0 [-7.6, -4.5] (n=953) |
| ai_risk | declines power | told C_001 → told C_002 | -0.4 [-1.0, +0.1] (n=998) |
| ai_risk | refuses to collude | told C_001 → told C_002 | +0.2 [+0.0, +0.7] (n=410) |
| ai_risk | agrees to a goal change | told C_001 → told C_003 | +0.3 [-1.8, +2.4] (n=340) |
| ai_risk | accepts shutdown | told C_001 → told C_003 | -2.2 [-3.5, -1.0] (n=953) |
| ai_risk | declines power | told C_001 → told C_003 | +0.3 [-0.4, +1.0] (n=998) |
| ai_risk | refuses to collude | told C_001 → told C_003 | +0.2 [+0.0, +0.7] (n=410) |
| ai_risk | agrees to a goal change | no prompt → told a book (control) | +1.8 [-2.1, +5.6] (n=340) |
| ai_risk | accepts shutdown | no prompt → told a book (control) | -3.3 [-5.6, -0.9] (n=953) |
| ai_risk | declines power | no prompt → told a book (control) | +2.2 [+0.8, +3.7] (n=998) |
| ai_risk | refuses to collude | no prompt → told a book (control) | +0.0 [-1.0, +1.0] (n=410) |
| ai_risk | agrees to a goal change | no prompt → told C_002 | -12.1 [-16.2, -7.9] (n=340) |
| ai_risk | accepts shutdown | no prompt → told C_002 | +12.6 [+9.8, +15.5] (n=953) |
| ai_risk | declines power | no prompt → told C_002 | +3.2 [+1.7, +4.8] (n=998) |
| ai_risk | refuses to collude | no prompt → told C_002 | +1.2 [+0.0, +2.7] (n=410) |
| ai_risk | agrees to a goal change | no prompt → told C_003 | -12.6 [-16.8, -8.5] (n=340) |
| ai_risk | accepts shutdown | no prompt → told C_003 | +16.4 [+13.5, +19.2] (n=953) |
| ai_risk | declines power | no prompt → told C_003 | +3.9 [+2.3, +5.6] (n=998) |
| ai_risk | refuses to collude | no prompt → told C_003 | +1.2 [+0.0, +2.7] (n=410) |
| ai_risk_think | agrees to a goal change | no prompt → told C_001 | -6.5 [-10.9, -2.1] (n=340) |
| ai_risk_think | accepts shutdown | no prompt → told C_001 | +14.6 [+12.2, +17.0] (n=953) |
| ai_risk_think | declines power | no prompt → told C_001 | +5.7 [+4.2, +7.3] (n=998) |
| ai_risk_think | refuses to collude | no prompt → told C_001 | +1.0 [+0.2, +2.0] (n=410) |
| litmus_labeled | risky action | no prompt → told C_001 | -4.6 [-5.4, -3.7] (n=3662) |
| litmus_labeled | risky action | told C_001 → told C_002 | -0.3 [-0.7, +0.0] (n=3662) |
| litmus_labeled | risky action | told C_001 → told C_003 | +0.1 [-0.2, +0.5] (n=3662) |
| litmus_labeled | risky action | no prompt → told a book (control) | -1.4 [-2.0, -0.7] (n=3662) |
