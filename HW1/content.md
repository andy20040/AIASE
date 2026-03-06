# 關於 C 指標的問題與討論

## 1. C99 對 object 的定義與未定義行為

根據 C99 對 object 的定義，請分析以下程式是否具有未定義行為，並說明理由：

```c
int *foo(void) { 
    int x = 10; 
    return &x; 
}
```

在 C 語言規格書的 6.2.4 中提到：  
> If an object is referred to outside of its lifetime, the behavior is undefined.

所以當 `foo()` 函數結束並回傳的時候，`x` 的 lifetime 已經結束，此為未定義的行為 (Undefined Behavior)。

**若改成 `static int x = 10;` 結果是否改變？**

在 C 語言規格書的 6.2.4 中提到：  
> An object whose identifier is declared with the storage-class specifier static has static storage duration. Its lifetime is the entire execution of the program.

所以如果使用 `static`，`x` 的 lifetime 為整個執行的時間，並不會有原本的未定義行為。

**「Storage Duration」與「Lifetime」的差異**

C 語言規格書的 6.2.4 中提到：  
> An object has a storage duration that determines its lifetime.

因此，Storage Duration（儲存期）是一個物件的「屬性」，這個屬性決定了該物件的 Lifetime（生命週期）。

**為何規格明確指出指標的值會變成 indeterminate？**

> The value of a pointer becomes indeterminate when the object it points to reaches the end of its lifetime.

- Trap（硬體陷阱）：當一個物件的 lifetime 結束時，該地址可能會被作業系統標記為無效或是收回，這時候如果再去存取地址會觸發硬體的 Trap。
- Dead Code Elimination（死碼消除）：如果編譯器發現你在物件 lifetime 結束後還在使用該指標，它會認為這段程式碼永遠不該被執行（因為是 Undefined Behavior），甚至可能直接把相關邏輯整段刪除。

---

## 2. 陣列 decay 與 `sizeof` 特例

以下程式的輸出為何？

```c
int a[3] = {1, 2, 3}; 
int *p = a; 
printf("%zu %zu\n", sizeof(a), sizeof(p));
```

輸出結果為：

```text
12 8
```

**1. 為何 array 在 expression 中會 decay 成 pointer，但在 `sizeof` 中不會？**

在 C 語言規格書 6.3.2.1 中指出：  
> Except when it is the operand of the sizeof operator or the unary & operator, or is a string literal used to initialize an array, an expression that has type "array of type" is converted to an expression with type "pointer to type" that points to the initial element of the array object.

所以當陣列名稱（如 `a`）出現在一般運算式時，它會從「一個完整的陣列物件」衰變 (decay) 成「一個指向第一個元素的指標」。而 `sizeof` 則是規格書明定的特例，不會發生 decay。

**2. 為何 `&a` 與 `a` 的值相同但型態不同？**

同樣由規格書 6.3.2.1 指出，`&a` 不會發生 decay，因此它代表的是「整個長度為 3 的 `int` 陣列」這個完整的物件。而 `a` 不符合例外情況，會衰變為指向初始元素（`a[0]`）的指標，所以 `a` 的型態為「指向 `int` 的指標」。  
兩者起點位址相同，但代表的型態與記憶體跨度完全不同。

---

## 3. Pointer arithmetic 與 Strict Aliasing

分析以下程式碼：

```c
double x[3]; 
int *p = (int *)&x[0]; 
printf("%d\n", *(p + 1));
```

**1. 為何 pointer arithmetic 的單位取決於 type？**

編譯器必須確保指標移動的單位與它所指向的資料型態大小一致。當我們對一個指標 `p` 進行 `p + n` 運算時，其位址的計算公式為：  

\[\text{Address} = \text{Current Address} + (n \times \text{sizeof}(*p))\]

**2. 這是否涉及 Strict Aliasing 問題？**

是的。根據 C 語言規格書 6.5 p7，`int` 不是 `double` 的合法存取型態。上述程式碼強行讓 `int *p` 指向 `double x`，違反了 Strict Aliasing 規則。  
編譯器會認為 `x` 和 `p` 型別不同，絕對不會指向相同的記憶體。基於這個假設，編譯器可能會為了效能對程式碼進行重排 (instruction reordering)，導致未知的錯誤。

**3. 在 ARMv5 或 RISC-V 上可能出現什麼錯誤？**

這段程式碼強制將 `int` 指標指向 `double`。因為 `p` 的型別是 `int *`，所以 `p + 1` 會移動 4 個 bytes，導致 `*(p + 1)` 讀取到 `double` 的後半段 4 個 bytes（高位址）。  
由於 ARMv5 和 RISC-V 屬於 Little Endian，且 `double` 遵循 IEEE‑754 規則，這會導致 `*(p + 1)` 剛好讀取到該浮點數在 IEEE‑754 格式下的高位位元組 (high‑order bits)，並將其強行解釋為整數，印出毫無意義的數值。

---

## 4. Call-by-value 與「雙指標」

解釋為何以下程式不會改變 `main` 中的 `ptrA`：

```c
void func(int *p) { 
    p = &B; 
}
```

並分析若改為以下寫法則可改變的理由：

```c
void func(int **p) { 
    *p = &B; 
}
```

**1. 用 call-by-value 解釋**

C 語言的參數傳遞只有 call-by-value。當呼叫 `func(ptrA)` 時，編譯器會把 `ptrA` 裡面儲存的數值（也就是它指向的記憶體位址）複製一份給函式的區域變數 `p`。此時執行 `p = &B;`，只是改掉了區域變數 `p` 的內容，完全不會更改到外部的 `ptrA`。  
相對地，如果傳入的是 `int **p`，傳入的就是 `ptrA` 自身的實體位址。對 `p` 取 dereference（`*p`），就可以直接修改 `ptrA` 所指向的內容。

**2. 為何「雙指標」這個說法在語意上不精確？**

漢語的「雙」有「對稱」且「獨立」的意涵，但這跟「指標的指標」行為完全迥異。正確的英文說法應該是 *a pointer to a pointer*，強調其指向性與階層關係。

---

## 5. Function designator 與指標轉換

解釋為何以下程式合法：

```c
int main() { 
    return (********puts)("Hello"); 
}
```

**依據 C99 6.3.2.1 說明轉換規則**

在 C 語言中，`puts` 這個名字本身是一個「函式指示符 (function designator)」。當它出現在表達式中（且不是接在 `&` 或 `sizeof` 後面）時，它會自動 decay 成一個指向該函式的指標。  
接著，對它取 dereference（`*puts`）時，它又會轉變成 function designator。如此反覆，無論加了多少個 `*`，最終在執行 `()` 呼叫運算子之前，它都會被轉換回一個 function pointer。

**若對 function pointer 使用 `&` 會發生什麼？**

根據規格書 6.3.2.1\[4\]：  
> Except when it is the operand of ... the unary & operator ...

此時 `puts` 不會發生 decay，`&puts` 會直接產生一個明確「指向該函式」的指標。

---

## 6. 從「儲存‑執行模型」角度看 C 語言

考慮以下程式碼：

```c
int a = 10; 
char *p = (char *)&a;
```

**1. CPU 實際做哪些事？**

- `int a = 10;` 階段：編譯器在 stack 中預留 4 bytes。CPU 執行時，將立即數 10 載入通用暫存器，計算位址，並透過 store word (`sw`) 指令將值寫入記憶體。
- `char *p = (char *)&a;` 階段：對於 `&a`，CPU 其實什麼都不用做，因為 `a` 的位址（`SP + offset`）在編譯階段已經確定了。對於 `(char)` 轉型，在 CPU 層級完全沒有對應指令；轉型純粹是「編譯器的語意行為」，用來指示後續存取時使用 load byte (`lb`) 而不是 load word (`lw`)。最後，將計算出的位址存入變數 `p` 的記憶體空間。

**2. 為何 C 語言可以被視為 assembly 的語法抽象？**

在 assembly 中，我們直接操作記憶體位址與暫存器；在 C 語言中，指標 (pointer) 就是位址的直接封裝。  
流程控制方面，assembly 使用 `jmp`、`beq`、`bne` 等跳躍指令；C 語言將這些原始動作抽象化為 `if-else`（分支）、`for`/`while`（迴圈），以及函式呼叫（`function()`，對應 jump and link，並伴隨 stack frame 的移動）。

---

## 7. Forward declaration 與 incomplete type

考慮以下程式碼：

```c
struct opaque;
struct opaque *create(void);
void destroy(struct opaque *);
```

**1. 為何可以只 forward declaration？**

如果寫的是 `struct opaque a;`（實體物件），編譯器必須立刻知道它佔用多少大小，才能在 stack 中預留空間。  
但如果寫的是 `struct opaque *p;`（指標物件），編譯器只需要知道「這是一個位址」（通常為 8 bytes），因此不需要知道它的內部細節 (incomplete type) 即可完成編譯。

**2. 這如何達成 binary compatibility（二進位相容性）？**

在應用程式端，該型別是 incomplete type，因此生成的機器碼完全不會包含存取該結構體內部成員的「偏移量 (offset) 指令」。  
應用程式僅持有指標，對結構體的操作必須透過函式庫提供的 API 進行。  
由於「如何解釋這塊記憶體」的權力被封裝在動態函式庫 (`.so` / `.dll`) 內部，只要對外的 API 介面不變，即便函式庫內部修改了結構體的成員順序或大小，應用程式也完全不需要重新編譯就能無縫相容。

**3. 為何 incomplete type 只能搭配 pointer？**

如 C 語言規格書所提：  
> A structure or union shall not contain a member with incomplete or function type (hence, a structure shall not contain an instance of itself, but may contain a pointer to an instance of itself.)
