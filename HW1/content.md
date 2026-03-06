根據 C99 對 object 的定義，請分析以下程式是否具有未定義行為，並說明理由 `int *foo(void) { int x = 10; return &x; }`
&emsp;&emsp;在 C 語言規格書的 6.2.4 中提到 :
>If an object is referred to outside of its
    lifetime, the behavior is undefined.

&emsp;&emsp;所以當 foo() 函數結束並回傳的時候x的lifetime已經結束，為未定義的行為
    1. 若改成 `static int x = 10;` 結果是否改變？
&emsp;&emsp;&emsp;&emsp;在C語言規格書的 6.2.4 中提到 :
>with the storage-class specifier static has static storage duration. Its lifetime is the entire execution of the program

&emsp;&emsp;所以如果使用 static ， x 的 lifetime 為整個執行的時間，並不會有原本的未定義行為
    2. 請用「storage duration」與「lifetime」兩個術語解釋差異。
C語言規格書的 6.2.4中提到
>An object has a storage duration that determines its lifetime.

&emsp;&emsp;因此 storage duration 是一個物件的屬性決定了他的 lifetime


3. 為何規格明確指出：
> The value of a pointer becomes indeterminate when the object it points to reaches the end of its lifetime.

* Trap: 當一個物件的 lifetime 結束時，該地址可能會被作業系統標記為無效或是收回，這時候如果再去存取地址會觸發硬體的 Trap 
* Dead Code Elimination : 如果編譯器發現你在物件 Lifetime 結束後還在使用該指標，它會認為這段程式碼永遠不該被執行（因為是 Undefined Behavior），甚至可能直接把相關邏輯整段刪掉。
- [ ] 以下程式的輸出為何？ `int a[3] = {1,2,3}; int *p = a; printf("%zu %zu\n", sizeof(a), sizeof(p));`
輸出為
    ```
    12 8
    ```
&emsp;&emsp;1. 為何 array 在 expression 中會 decay 成 pointer，但在 sizeof 中不會？
    
&emsp;&emsp;&emsp;在C語言規格書中 6.3.2.1 中指出
 >Except when it is the operand of the sizeof operator or the unary & operator, or is a string literal used to initialize an array, an expression that has type ‘‘array of type’’ is converted to an expression with type ‘‘pointer to type’’ that points to the initial element of the array object.

&emsp;&emsp;&emsp;所以陣列名（如 a）時，它會從「一個完整的陣列物件」衰變成「一個指向第一個元素的指標」。而 sizeof 是特例
&emsp;&emsp;2. 為何 `&a` 與 `a` 的值相同但型態不同？
&emsp;&emsp;&emsp;同樣由 C 語言規格書 6.3.2.1 指出， &a 不會發生 decay 因此它代表「整個長度為 3 的 int 陣列」這個物件。而 a 不符合書中提到的例外情況，因此會從原本的「陣列型態」衰變為「指標型態」，並且指向「初始元素（initial element）」。而陣列「初始元素」是 a[0]，所以 a 為指向 int 的指標。
- [ ] 分析： `double x[3]; int *p = (int *)&x[0]; printf("%d\n", *(p+1));`
    1. 為何 pointer arithmetic 的單位取決於 type？
    編譯器必須確保指標移動的單位與它所指向的資料型態大小一致。當我們對一個指標 $p$ 進行 $p + n$ 運算時，其位址的計算公式為：
$$\text{Address} = \text{Current Address} + (n \times \text{sizeof}(*p))$$
    3. 這是否涉及 strict aliasing 問題？
    根據C語言規格書 6.5 p7，int 不是 double 的合法存取型態。上述程式碼強行讓 $int\ *p$ 指向 $double \ x$，涉及了strict aliasing的問題，而編譯器認為$x$ 和 $p$ 的型別不同，所以 x 和 p 不會指向相同的記憶體，既然位址不同，對 $*x$ 寫入資料不會改變 $*p$ 的位址，而編譯器會為了效能對程式碼進行重排
    4. 在 ARMv5 或 RISC-V 上可能出現什麼錯誤？
    這段程式碼強制將 int 的指標去指向一個 double ，而因為 p 的型別是 int* 所以 p+1 會移動4個byte，因此 *(p+1) 會讀取到 double 的後半段的 4 個 byte (高位址） ，而 ARMv5 和 RISC-V屬於Little Endian，而double 的儲存方式遵循 IEEE-754 的規則，這會導致 *(p+1) 讀取到該 double 數值在 IEEE 754 格式下的高位位元組（High-order bits），並被強行解釋為整數，導致結果在數值上毫無意義。
- [ ] 解釋為何以下程式不會改變 main 中的 ptrA： `void func(int *p) { p = &B; }` 並分析 `void func(int **p) { *p = &B; }`
    1. 用 call-by-value 解釋
    因為參數傳遞的方式是 call-by-value 所以當呼叫 func(ptrA) 時，編譯器會把 ptrA 裡面儲存的數值（也就是它所指向的記憶體位址）複製一份給函式的區域變數 p 。此時執行 p = &B 時，只是改掉了 func 區域變數 p 的內容，讓它指向 B ，完全不會去更改到 ptrA 
    相對的如果傳入的是 `int **p`則傳入的是 ptrA 的位址，然後對 p 取 dereference這樣就可以更改ptrA所指向的位址

    5. 為何「雙指標」這個說法在語意上不精確？
        根據[你所不知道的C語言：指標篇](https://hackmd.io/@sysprog/c-pointer)中所提到：
        漢語的「雙」有「對稱」且「獨立」的意含，但這跟「指標的指標」行為完全迥異
        正確的說法應該為 a pointer of a pointer
- [ ] 解釋為何以下程式合法： `int main() { return (********puts)("Hello"); }`
    1. 依據 C99 6.3.2.1 說明 function designator 的轉換規則。
    在C語言規格書中 6.3.2.1 中指出
 >Except when it is the operand of the sizeof operator or the unary & operator, or is a string literal used to initialize an array, an expression that has type ‘‘array of type’’ is converted to an expression with type ‘‘pointer to type’’ that points to the initial element of the array object.

在 C 語言中，puts 這個名字本身是一個「函式指示符（Function Designator）」當它出現在表達式中（且不是接在 & 或 sizeof 後面）時，它會自動 decay 成一個指向該函式的指標。因此原本 puts 是一個 function designator 它會decay 成 function pointer ，而又在對它取 dereference *puts 又會轉變成 function designator 如此反覆
因此無論加了多少個 *，最終在執行 () 呼叫運算子之前，它都會被轉換回一個 Function pointer
    &emsp;&emsp;&emsp;2. 為何 `*` 的數量不影響結果？ 同上
    &emsp;&emsp;&emsp;3. 若對 function pointer 使用 `&` 會發生什麼？
    根據規格書 6.3.2.1[4] :
>"Except when it is the operand of ... the unary & operator"。

此時 puts 不會發生 decay ， &puts 會直接產生一個指向該函式的指標。
- [ ] 從「儲存-執行模型」角度解釋 `int a = 10; char *p = (char *)&a;`
    1. CPU 實際做哪些事？
    在`int a = 10;` 的階段中，編譯器會在堆疊中為 a 預留空間（假設是 4 bytes）。CPU 指令執行：Load Immediate: CPU 將 $10$載入到一個通用暫存器。Address Calculation: 計算 a 的記憶體位址。Store: 執行 Store Word (sw) 指令，將暫存器中的值寫入該記憶體位址。
    在`char *p = (char *)&a; `的階段 &a CPU 其實什麼都不用做，因為在上一段指令中，a 的位址（SP + Offset）已經在暫存器或編譯階段確定了。(char) (轉型)：這在 CPU 層級完全沒有對應指令。 轉型是「編譯器的語義行為」。它告訴編譯器：「透過 p 去讀資料，要用 lb (Load Byte) 而不是 lw (Load Word)。」
    CPU 指令執行：
Address Copy: 將剛才計算出的 a 的位址存入另一個記憶體空間（變數 p 的位置）。
    2. 為何 C 語言可以被視為 assembly 的語法抽象？
    在 Assembly 中，直接操作記憶體位址；在 C 語言中，指標（Pointer） 就是位址的直接封裝。
    在Assembly 使用 jmp, beq, bne 等跳躍指令來控制流程。C 語言將這些原始動作抽象化為：if-else $\rightarrow$ 分支（Branch）。for/while $\rightarrow$ 迴圈跳躍與條件判斷。function() $\rightarrow$ Jump and Link，伴隨 Stack Frame 的移動。
- [ ] 考慮以下程式碼:
    ```c
    struct opaque;
    struct opaque *create(void);
    void destroy(struct opaque *);
    ```
    1. 為何可以只 forward declaration？
        實體物件： 如果寫的是 `struct opaque a;`，編譯器必須立刻知道 `struct opaque` 佔用多少大小，才能在 Stack 中預留空間。
指標物件： 如果寫 struct opaque *p;，編譯器只需要知道「這是一個位址」。
因此，只要宣告「指向它的指標」，編譯器就不需要知道它的內部細節（Incomplete Type）。
而上方的程式碼 create 的是物件的指標
    2. 這如何達成 binary compatibility？
在應用程式端，由於只有 struct opaque; 的  Forward Declaration，該型別在編譯器眼中是 Incomplete Type。因此，應用程式生成的機器碼無法、也不會包含任何存取該結構體內部成員的篇一量指令。
而應用程式僅持有指標（一個 8 Bytes 的地址），對結構體的所有操作都必須透過函式庫提供的 API來進行。也就是「如何解釋這塊記憶體」的權力被完全封裝在動態函式庫 (.so 或 .dll) 內部。
只要函式庫對外的 API 介面（ABI）保持不變，即便函式庫內部修改了結構體的大小、成員順序或內容，也只會改變函式庫內部的 Offset 指令。應用程式端的機器碼因為從頭到尾都沒經手這些細節，所以不需要重新編譯就能直接相容新版的函式庫。
    3. 為何 incomplete type 只能搭配 pointer？
    C 語言規格書中提到:
>A structure or union shall not contain a member with incomplete or function type (hence,
a structure shall not contain an instance of itself, but may contain a pointer to an instance